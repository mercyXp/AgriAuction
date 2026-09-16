# Backup and recovery

A working AgriAuction database holds farmers, lots, bids, sales and payments. Disk failure, a bad `UPDATE`, or a failed experiment during a viva can destroy that history. Backups are how you get it back.

Do **not** put real passwords in scripts or in Git.

---

## 1. Why backups are necessary

- Hardware or VM failure on a laptop or on Railway
- Accidental `DELETE` / `DROP` during a demonstration
- Need to restore the seed database to a known state before marking

## 2. What is backed up

`mysqldump` copies **data and schema** for the `agriauction` database:

- tables, views, stored procedures, triggers (if any)
- rows (farmers, lots, bids, sales, …)

It does **not** copy MySQL users created by `security.sql`. Recreate those from `database/security.sql` after a full server rebuild.

Store dump files **outside** the Git repo (for example `C:\AgriAuction-backups\`). Dumps can contain personal demo data; they are not source code.

## 3. Create a backup (placeholder password)

Windows PowerShell, from a folder you control:

```powershell
New-Item -ItemType Directory -Force -Path C:\AgriAuction-backups | Out-Null
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe" `
  -u agriauction_admin -pYOUR_ADMIN_PASSWORD `
  --routines --single-transaction --databases agriauction `
  > C:\AgriAuction-backups\agriauction-YYYYMMDD.sql
```

Replace `YOUR_ADMIN_PASSWORD` with the password you set when loading `security.sql`. Do not commit that value.

`--routines` includes `sp_close_auction` and `sp_record_payment`.  
`--single-transaction` takes a consistent InnoDB snapshot without locking the whole database for long.

macOS / Linux:

```bash
mysqldump -u agriauction_admin -p \
  --routines --single-transaction --databases agriauction \
  > "$HOME/agriauction-backups/agriauction-$(date +%Y%m%d).sql"
```

## 4. Where the backup is stored

Local course work: a dated `.sql` file on your disk or USB, **not** in the project folder that you push to GitHub.

Railway: use Railway’s MySQL plugin backup/export if the platform offers it, **and** keep your own `mysqldump` before a marking demo.

## 5. How to restore

```powershell
Get-Content -Raw C:\AgriAuction-backups\agriauction-YYYYMMDD.sql |
  & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u agriauction_admin -pYOUR_ADMIN_PASSWORD
```

Or:

```bash
mysql -u agriauction_admin -p agriauction < agriauction-YYYYMMDD.sql
```

If the dump starts with `CREATE DATABASE` / `USE agriauction`, restoring onto an empty server recreates the schema. If you only dumped tables, create the database first.

## 6. Verify the restored database

```sql
USE agriauction;
SHOW TABLES;
SELECT COUNT(*) AS farmers FROM farmers;
SELECT COUNT(*) AS lots FROM produce_lots;
SELECT COUNT(*) AS sales FROM successful_sales;
SHOW CREATE PROCEDURE sp_close_auction;
SELECT lot_number, status FROM produce_lots WHERE status = 'OPEN';
```

Compare the counts with what you recorded when you took the dump. Log into the Flask app and open Dashboard — the cards should match the SQL counts.

---

## Application vs MySQL users (do not confuse them)

Restoring tables restores **staff** rows (who can log into the website). It does not recreate `agriauction_app`. After a full MySQL reinstall, run `database/security.sql` again, then put the app password in `.env`.
