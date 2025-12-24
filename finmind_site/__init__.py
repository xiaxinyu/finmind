import os
if os.environ.get("DB_ENGINE", "mysql").lower() == "mysql":
    import pymysql
    pymysql.install_as_MySQLdb()
