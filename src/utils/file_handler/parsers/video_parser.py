import av
from io import BytesIO
from typing import Optional
from RAW.modals import Image
from RAW.llms import BaseLLM
import numpy as np
import cv2
import filetype

async def video_parser(video_data: bytes, llm: Optional[BaseLLM] = None, fps: float = 1) -> str:
    """Extract frames from a video at specified fps and use LLM to describe the content."""
    if not isinstance(video_data, bytes):
        raise TypeError(f"Expected bytes for video_data, got {type(video_data)}")

    if not video_data:
        raise ValueError("video_data is empty")

    if fps <= 0:
        raise ValueError(f"fps must be positive, got {fps}")

    if llm is None:
        raise ValueError("LLM instance is required for video parsing")

    # Validate video format
    kind = filetype.guess(video_data)
    if not kind or kind.mime not in {"video/mp4", "video/avi", "video/mpeg"}:
        raise ValueError(f"Unsupported or invalid video format. Detected MIME: {kind.mime if kind else 'Unknown'}. Expected: video/mp4, video/avi, video/mpeg")

    # Load video from bytes using pyav
    video_stream = BytesIO(video_data)
    try:
        container = av.open(video_stream)
    except Exception as e:
        raise ValueError(f"Failed to initialize AV container: {str(e)}")

    # Get video stream
    video_stream = next((s for s in container.streams if s.type == 'video'), None)
    if not video_stream:
        raise ValueError("No video stream found in container")

    # Get video properties
    video_fps = float(video_stream.average_rate or video_stream.rate)
    if video_fps <= 0:
        raise ValueError("Invalid video FPS")

    total_frames = video_stream.frames or int(video_stream.duration * video_fps / video_stream.time_base)
    if total_frames <= 0:
        raise ValueError("Invalid video frame count")

    # Calculate frame interval based on desired fps
    frame_interval = max(1, int(video_fps / fps))  # Frames per interval
    frames = []

    if fps == 1:
        # For fps=1, pick the middlemost frame of each second
        num_seconds = total_frames / video_fps
        for second in range(int(num_seconds) + 1):
            middle_frame_time = second + 0.5  # Middle of the second
            middle_frame_idx = int(middle_frame_time * video_fps)
            if middle_frame_idx < total_frames:
                try:
                    container.seek(int(middle_frame_time * video_stream.time_base.denominator), stream=video_stream)
                    frame_idx = 0
                    for frame in container.decode(video=0):
                        if frame_idx >= middle_frame_idx:
                            frame_np = frame.to_ndarray(format='bgr24')
                            _, frame_bytes = cv2.imencode('.jpg', frame_np)
                            frames.append(Image.from_bytes(frame_bytes.tobytes()))
                            break
                        frame_idx += 1
                except Exception as e:
                    raise ValueError(f"Failed to extract frame at {middle_frame_time}s: {str(e)}")
    else:
        # For other fps values, use uniform sampling
        frame_idx = 0
        for frame in container.decode(video=0):
            if frame_idx % frame_interval == 0:
                try:
                    frame_np = frame.to_ndarray(format='bgr24')
                    _, frame_bytes = cv2.imencode('.jpg', frame_np)
                    frames.append(Image.from_bytes(frame_bytes.tobytes()))
                except Exception as e:
                    raise ValueError(f"Failed to extract frame {frame_idx}: {str(e)}")
            frame_idx += 1

    container.close()

    if not frames:
        raise ValueError("No frames extracted from video")

    # Use LLM to describe the video
    prompt = "Describe what the video shows based on the provided frames."
    print("""Using LLM to process video frames...""")
    result = await llm.generate(prompt=prompt, images=frames, stream=False)

    if not isinstance(result, str):
        raise ValueError(f"Expected string response from LLM, got {type(result)}")

    return result.strip()