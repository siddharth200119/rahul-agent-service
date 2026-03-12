from yoyo import step

__depends__ = {"20260305_01_K1TNj-ocr-queue"}

steps = [
    step(
        "ALTER TABLE conversations ADD COLUMN metadata JSONB DEFAULT '{}'::jsonb;",
        "ALTER TABLE conversations DROP COLUMN IF EXISTS metadata;"
    )
]
