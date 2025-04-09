Generic single-database configuration.

* **生成版本:**

```bash
alembic revision --autogenerate -m "Add email column to users table"
```

* **应用所有未应用的迁移:**
  ```bash
  alembic upgrade head
  ```
  `head` 指的是最新的迁移版本。Alembic 会查找当前数据库版本（记录在 `alembic_version` 表中），然后按顺序执行从当前版本到
  `head` 之间的所有 `upgrade()` 函数。

* **应用到特定版本:**
  ```bash
  alembic upgrade <revision_id> # 例如 alembic upgrade xxxxxxxxxxxx
  ```
  这会将数据库模式更新到指定的 `revision_id` 版本。如果目标版本比当前版本旧，它实际上会执行 `downgrade` 操作。

* **只应用下一个版本:**
  ```bash
  alembic upgrade +1
  ```
* **回滚到上一个版本:**
  ```bash
  alembic downgrade -1
  ```

* **回滚到指定版本:**
  ```bash
  alembic downgrade <revision_id>
  ```

* **回滚所有迁移（回到初始状态）:**
  ```bash
  alembic downgrade base
  ```
  `base` 指的是没有任何迁移应用的状态。