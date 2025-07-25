import sqlite3
print("SQLite version:", sqlite3.sqlite_version)
print("SQLite version info:", sqlite3.sqlite_version_info)
print("Check result:", sqlite3.sqlite_version_info < (3, 35, 0))
print("is_client value:", is_client)
print("IN_COLAB value:", IN_COLAB)