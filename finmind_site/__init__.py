import os
if os.environ.get("DB_ENGINE", "sqlite").lower() == "mysql":
    import pymysql
    pymysql.install_as_MySQLdb()
