
-- ============================================================
-- FDE ENTERPRISE SECURITY & SEMANTIC LAYER
-- Database: ColdChainLogistics
-- Run as an administrator, not as USR_FDE_RO.
-- ============================================================

USE ColdChainLogistics;
GO

-- 1. Confirm the existing server login is available.
IF SUSER_ID(N'USR_FDE_RO') IS NULL
BEGIN
    THROW 50001,
        'USR_FDE_RO login is missing. Create the login securely first.',
        1;
END;
GO

-- 2. Create the semantic schema only if it is missing.
IF SCHEMA_ID(N'FDE_VIEWS') IS NULL
BEGIN
    EXEC(N'CREATE SCHEMA FDE_VIEWS AUTHORIZATION dbo;');
END;
GO

-- 3. Update the view safely instead of creating a duplicate.
CREATE OR ALTER VIEW FDE_VIEWS.VW_ACTIVE_FLEET
AS
SELECT
    TS_UTC AS [Timestamp],
    V_LAT AS [Latitude],
    V_LON AS [Longitude],
    CAST(IOT_TEMP_VAL_C AS FLOAT) AS [Current_Temperature_C],
    CGO_COND_CD AS [Cargo_Condition_Code],
    RISK_CLS_TXT AS [Risk_Classification],
    DELAY_PROB_DEC AS [Delay_Probability],
    PRT_CNG_LVL AS [Port_Congestion_Level],
    RT_RSK_IDX AS [Route_Risk_Index]
FROM dbo.TBL_SC_FLEET_HIST_RAW;
GO

-- 4. Create the database user only if it is missing.
IF USER_ID(N'USR_FDE_RO') IS NULL
BEGIN
    CREATE USER USR_FDE_RO FOR LOGIN USR_FDE_RO;
END;
GO

-- 5. Apply the intended permissions.
GRANT SELECT
    ON OBJECT::FDE_VIEWS.VW_ACTIVE_FLEET
    TO USR_FDE_RO;

DENY SELECT
    ON OBJECT::dbo.TBL_SC_FLEET_HIST_RAW
    TO USR_FDE_RO;

DENY INSERT, UPDATE, DELETE, ALTER
    ON SCHEMA::dbo
    TO USR_FDE_RO;
GO

-- 6. Report the objects and permissions for verification.
SELECT
    DB_NAME() AS CurrentDatabase,
    SCHEMA_ID(N'FDE_VIEWS') AS SemanticSchemaId,
    OBJECT_ID(N'FDE_VIEWS.VW_ACTIVE_FLEET', N'V')
        AS SemanticViewObjectId,
    USER_ID(N'USR_FDE_RO') AS ReadOnlyUserId;
GO
