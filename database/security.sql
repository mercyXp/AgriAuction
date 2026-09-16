-- AgriAuction MySQL users and privileges
-- Phase 6: least-privilege database accounts
--
-- Load after database/schema.sql so the agriauction database exists.
-- Run as root (or another account that can CREATE USER and GRANT).
-- Passwords are NOT stored in this file and must never be committed to Git.
--
-- In the same session, set the three passwords FIRST, then load this file.
--
-- MySQL Workbench (run these three lines, then File → Run SQL Script on this file):
--   SET @app_password       = 'choose-a-strong-local-password';
--   SET @reporting_password = 'choose-a-strong-local-password';
--   SET @admin_password     = 'choose-a-strong-local-password';
--
-- PowerShell (from the project folder):
--   $mysql = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
--   Get-Content -Raw database\security.sql | & $mysql -u root -p
--   (set the three variables in Workbench, or paste them above the SOURCE)
--
-- Put the app password in gitignored .env as DB_PASSWORD.
-- Flask uses agriauction_app only. Do not point the web app at root or agriauction_admin.

USE agriauction;

DROP PROCEDURE IF EXISTS sp_install_mysql_users;

DELIMITER $$

CREATE PROCEDURE sp_install_mysql_users()
BEGIN
    IF @app_password IS NULL OR @app_password = '' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Set @app_password before running security.sql';
    END IF;

    IF @reporting_password IS NULL OR @reporting_password = '' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Set @reporting_password before running security.sql';
    END IF;

    IF @admin_password IS NULL OR @admin_password = '' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Set @admin_password before running security.sql';
    END IF;

    -- localhost (named pipe / socket) and 127.0.0.1 (TCP).
    -- mysql-connector-python on Windows usually connects over TCP.

    SET @sql = CONCAT(
        'CREATE USER IF NOT EXISTS ',
        QUOTE('agriauction_app'), '@', QUOTE('localhost'),
        ' IDENTIFIED BY ', QUOTE(@app_password)
    );
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    SET @sql = CONCAT(
        'CREATE USER IF NOT EXISTS ',
        QUOTE('agriauction_app'), '@', QUOTE('127.0.0.1'),
        ' IDENTIFIED BY ', QUOTE(@app_password)
    );
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    SET @sql = CONCAT(
        'ALTER USER ',
        QUOTE('agriauction_app'), '@', QUOTE('localhost'),
        ' IDENTIFIED BY ', QUOTE(@app_password)
    );
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    SET @sql = CONCAT(
        'ALTER USER ',
        QUOTE('agriauction_app'), '@', QUOTE('127.0.0.1'),
        ' IDENTIFIED BY ', QUOTE(@app_password)
    );
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    SET @sql = CONCAT(
        'CREATE USER IF NOT EXISTS ',
        QUOTE('agriauction_reporting'), '@', QUOTE('localhost'),
        ' IDENTIFIED BY ', QUOTE(@reporting_password)
    );
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    SET @sql = CONCAT(
        'CREATE USER IF NOT EXISTS ',
        QUOTE('agriauction_reporting'), '@', QUOTE('127.0.0.1'),
        ' IDENTIFIED BY ', QUOTE(@reporting_password)
    );
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    SET @sql = CONCAT(
        'ALTER USER ',
        QUOTE('agriauction_reporting'), '@', QUOTE('localhost'),
        ' IDENTIFIED BY ', QUOTE(@reporting_password)
    );
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    SET @sql = CONCAT(
        'ALTER USER ',
        QUOTE('agriauction_reporting'), '@', QUOTE('127.0.0.1'),
        ' IDENTIFIED BY ', QUOTE(@reporting_password)
    );
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    SET @sql = CONCAT(
        'CREATE USER IF NOT EXISTS ',
        QUOTE('agriauction_admin'), '@', QUOTE('localhost'),
        ' IDENTIFIED BY ', QUOTE(@admin_password)
    );
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    SET @sql = CONCAT(
        'CREATE USER IF NOT EXISTS ',
        QUOTE('agriauction_admin'), '@', QUOTE('127.0.0.1'),
        ' IDENTIFIED BY ', QUOTE(@admin_password)
    );
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    SET @sql = CONCAT(
        'ALTER USER ',
        QUOTE('agriauction_admin'), '@', QUOTE('localhost'),
        ' IDENTIFIED BY ', QUOTE(@admin_password)
    );
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    SET @sql = CONCAT(
        'ALTER USER ',
        QUOTE('agriauction_admin'), '@', QUOTE('127.0.0.1'),
        ' IDENTIFIED BY ', QUOTE(@admin_password)
    );
    PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

    -- Strip any leftover privileges, then grant only what each account needs.
    REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'agriauction_app'@'localhost';
    REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'agriauction_app'@'127.0.0.1';
    REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'agriauction_reporting'@'localhost';
    REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'agriauction_reporting'@'127.0.0.1';
    REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'agriauction_admin'@'localhost';
    REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'agriauction_admin'@'127.0.0.1';

    -- Flask: read/write rows, call procedures, query views. No DDL.
    GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE, SHOW VIEW
        ON agriauction.*
        TO 'agriauction_app'@'localhost',
           'agriauction_app'@'127.0.0.1';

    -- Reports / viva SELECT demos: read only.
    GRANT SELECT, SHOW VIEW
        ON agriauction.*
        TO 'agriauction_reporting'@'localhost',
           'agriauction_reporting'@'127.0.0.1';

    -- Schema work in Workbench. Still not MySQL root (no CREATE USER, no *.*).
    GRANT ALL PRIVILEGES
        ON agriauction.*
        TO 'agriauction_admin'@'localhost',
           'agriauction_admin'@'127.0.0.1'
        WITH GRANT OPTION;
END$$

DELIMITER ;

CALL sp_install_mysql_users();

DROP PROCEDURE IF EXISTS sp_install_mysql_users;

-- Confirm what was granted (passwords are not shown).
SHOW GRANTS FOR 'agriauction_app'@'localhost';
SHOW GRANTS FOR 'agriauction_reporting'@'localhost';
SHOW GRANTS FOR 'agriauction_admin'@'localhost';
