# Huong Dan Dong Gop

Cam on ban da quan tam dong gop cho Research-Focused PKM.

## Nguyen tac bat buoc truoc khi code

Doc theo thu tu sau:

1. START_HERE_FOR_AI_AGENT.md
2. PKM_ARCHITECTURE.md
3. PKM_ROADMAP.md
4. PKM_SPEC_FINAL.md

## Quy tac ky thuat

- Giu dung stack hien tai: Python + PySide6 + SQLite + SQLAlchemy + Alembic.
- Khong them business logic vao UI widgets.
- Moi thay doi schema phai co Alembic migration.
- Moi extract phai co source anchor hop le.
- UI hien thi cho nguoi dung phai bang tieng Viet.

## Quy trinh de xuat

1. Tao branch theo dinh dang: feature/ten-ngan hoac fix/ten-ngan.
2. Viet code nho, tach ro trach nhiem.
3. Them hoac cap nhat test lien quan.
4. Chay test local:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

1. Cap nhat tai lieu neu thay doi architecture, schema, rules hoac roadmap.

## Quy tac pull request

- Tieu de ro rang, co boi canh va tac dong.
- Co mo ta cach test va ket qua.
- Neu co rui ro con lai, ghi ro trong PR.
- Uu tien PR nho, de review va rollback.

## Giay phep dong gop

Bang viec dong gop, ban dong y rang phan dong gop co the duoc phat hanh theo giay phep MIT cua du an.
