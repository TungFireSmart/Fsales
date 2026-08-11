# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# === MYSQL CONNECTOR: hidden imports bắt buộc ===
hidden_imports = [
    "mysql.connector.plugins.mysql_native_password",
    "mysql.connector.plugins.caching_sha2_password",
    "mysql.connector.locales",
    "mysql.connector.locales.eng",
]

# Thu toàn bộ submodules mysql.connector (an toàn)
hidden_imports += collect_submodules("mysql.connector")
hidden_imports += collect_submodules("docx")
hidden_imports += ["docx"]

# === PCCC consulting / survey modules imported dynamically ===
hidden_imports += [
    "version",
    "khao_sat_helpers",
    "khao_sat_data",
    "bien_ban_khao_sat",
    "mau_pccc",
]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        # === UI FORMS / PY MODULES ===
        ("UI\\*.py", "UI"),
        ("UI\\*.ui", "UI"),
        # === LOGO ASSETS ===
        ("assets/logo_pccc.png", "assets"),
        ("assets/logo_infutech.png", "assets"),
        ("assets/logo_bach_khoa.png", "assets"),
        ("styles/app.qss", "styles"),
        ("update_config.json", "."),
        ("bom_catalog.json", "."),

        # === EXCEL QUOTE TEMPLATES ===
        ("bao_gia_mau.xlsx", "."),
        ("bao_gia_mau_infutech.xlsx", "."),
        ("bao_gia_mau_bach_khoa.xlsx", "."),
        ("bao_gia_thue.xlsx", "."),

        # === CONTRACT TEMPLATE ===
        ("mau_hop_dong.docx", "."),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Fsales",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="fireman.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="Fsales",
)
