from yoyo import step

__depends__ = {"20260210_02_Xa9eZ-messagesmessages"}

steps = [
    step(
        """
        -- Sequences for IDs
        CREATE SEQUENCE IF NOT EXISTS so_analysis_seq START 1001;
        CREATE SEQUENCE IF NOT EXISTS pa_analysis_seq START 1001;

        -- Vendor Performance Analysis Table
        CREATE TABLE vendor_performance_analysis (
            id BIGSERIAL PRIMARY KEY,
            request_id VARCHAR(50) UNIQUE NOT NULL,
            grn_number VARCHAR(100) NOT NULL,
            report TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        -- SO Validation Analysis Table
        CREATE TABLE so_validation_analysis (
            id BIGSERIAL PRIMARY KEY,
            request_id VARCHAR(50) NOT NULL,
            product_id BIGINT NOT NULL,
            quantity DOUBLE PRECISION,
            weight DOUBLE PRECISION,
            status VARCHAR(50),
            message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX idx_so_validation_request_id ON so_validation_analysis(request_id);
        """,
        """
        DROP TABLE IF EXISTS so_validation_analysis;
        DROP TABLE IF EXISTS vendor_performance_analysis;
        DROP SEQUENCE IF EXISTS pa_analysis_seq;
        DROP SEQUENCE IF EXISTS so_analysis_seq;
        """
    )
]
