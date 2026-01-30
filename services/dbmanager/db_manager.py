"""
Database Manager Dashboard - Simple CRUD Interface
Dashboard sederhana untuk mengelola SQLite database dan JSON files
"""

import streamlit as st
import pandas as pd
import json
import sqlite3
from datetime import datetime
from pathlib import Path

# Konfigurasi halaman
st.set_page_config(
    page_title="Database Manager",
    page_icon="🗄️",
    layout="wide"
)

# Path database dan JSON
DB_PATH = "aeropon.db"
JSON_DIR = Path("data/conversations")

# Fungsi helper untuk database
def get_connection():
    """Buat koneksi ke database"""
    return sqlite3.connect(DB_PATH)

def get_tables():
    """Dapatkan daftar semua tabel"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def get_table_data(table_name, limit=100):
    """Dapatkan data dari tabel"""
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {limit}", conn)
    conn.close()
    return df

def get_table_schema(table_name):
    """Dapatkan schema tabel"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    schema = cursor.fetchall()
    conn.close()
    return schema

def delete_record(table_name, primary_key_col, primary_key_value):
    """Hapus record dari tabel"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE {primary_key_col} = ?", (primary_key_value,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected

def update_record(table_name, primary_key_col, primary_key_value, updates):
    """Update record di tabel"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Buat query UPDATE
    set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
    values = list(updates.values()) + [primary_key_value]
    
    query = f"UPDATE {table_name} SET {set_clause} WHERE {primary_key_col} = ?"
    cursor.execute(query, values)
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected

def insert_record(table_name, data):
    """Insert record baru ke tabel"""
    conn = get_connection()
    cursor = conn.cursor()
    
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    values = list(data.values())
    
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    cursor.execute(query, values)
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

# Fungsi helper untuk JSON
def get_json_files():
    """Dapatkan daftar file JSON"""
    if not JSON_DIR.exists():
        return []
    return sorted([f.name for f in JSON_DIR.glob("*.json")])

def read_json_file(filename):
    """Baca file JSON"""
    filepath = JSON_DIR / filename
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json_file(filename, data):
    """Tulis ke file JSON"""
    filepath = JSON_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def delete_json_file(filename):
    """Hapus file JSON"""
    filepath = JSON_DIR / filename
    filepath.unlink()

# Header
st.title("🗄️ Database Manager")
st.markdown("Dashboard sederhana untuk mengelola database SQLite dan file JSON")

# Sidebar untuk navigasi
st.sidebar.header("📋 Menu")
mode = st.sidebar.radio(
    "Pilih Mode",
    ["SQLite Database", "JSON Files"]
)

# ==================== MODE: SQLite Database ====================
if mode == "SQLite Database":
    st.header("📊 SQLite Database Manager")
    
    # Pilih tabel
    tables = get_tables()
    selected_table = st.selectbox("Pilih Tabel", tables)
    
    if selected_table:
        # Tabs untuk operasi
        tab1, tab2, tab3, tab4 = st.tabs(["📖 View", "➕ Create", "✏️ Update", "🗑️ Delete"])
        
        # TAB 1: VIEW
        with tab1:
            st.subheader(f"Data dari tabel: {selected_table}")
            
            # Limit records
            limit = st.slider("Jumlah data yang ditampilkan", 10, 500, 100)
            
            # Dapatkan data
            df = get_table_data(selected_table, limit)
            
            if not df.empty:
                st.dataframe(df, use_container_width=True, height=400)
                st.caption(f"Menampilkan {len(df)} baris dari tabel {selected_table}")
                
                # Download as CSV
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"{selected_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Tabel kosong")
        
        # TAB 2: CREATE
        with tab2:
            st.subheader(f"Tambah Data Baru ke: {selected_table}")
            
            # Dapatkan schema
            schema = get_table_schema(selected_table)
            
            st.markdown("**Schema Tabel:**")
            schema_df = pd.DataFrame(schema, columns=['ID', 'Name', 'Type', 'NotNull', 'Default', 'PK'])
            st.dataframe(schema_df, use_container_width=True)
            
            st.markdown("---")
            st.markdown("**Form Input:**")
            
            # Buat form input
            new_data = {}
            for col in schema:
                col_id, col_name, col_type, not_null, default_val, is_pk = col
                
                # Skip auto-increment primary key
                if is_pk and col_type.upper() == "INTEGER":
                    continue
                
                # Input field berdasarkan tipe
                if col_type.upper() in ["INTEGER", "NUMERIC"]:
                    new_data[col_name] = st.number_input(
                        f"{col_name} ({col_type})",
                        value=0 if not_null else None,
                        key=f"create_{col_name}"
                    )
                elif col_type.upper() == "BOOLEAN":
                    new_data[col_name] = st.checkbox(
                        f"{col_name} ({col_type})",
                        key=f"create_{col_name}"
                    )
                elif col_type.upper() in ["DATE", "DATETIME"]:
                    new_data[col_name] = st.text_input(
                        f"{col_name} ({col_type})",
                        value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        key=f"create_{col_name}"
                    )
                elif col_type.upper() == "JSON":
                    new_data[col_name] = st.text_area(
                        f"{col_name} ({col_type})",
                        value="{}",
                        key=f"create_{col_name}"
                    )
                else:
                    new_data[col_name] = st.text_input(
                        f"{col_name} ({col_type})",
                        value="" if not not_null else "",
                        key=f"create_{col_name}"
                    )
            
            if st.button("➕ Tambah Data", type="primary"):
                try:
                    # Convert JSON strings
                    for key, value in new_data.items():
                        col_info = next((c for c in schema if c[1] == key), None)
                        if col_info and col_info[2].upper() == "JSON" and isinstance(value, str):
                            new_data[key] = value  # Keep as string for SQLite
                    
                    last_id = insert_record(selected_table, new_data)
                    st.success(f"✅ Data berhasil ditambahkan! ID: {last_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # TAB 3: UPDATE
        with tab3:
            st.subheader(f"Update Data di: {selected_table}")
            
            # Dapatkan data
            df = get_table_data(selected_table, 100)
            
            if not df.empty:
                # Pilih record untuk di-update
                primary_key_col = df.columns[0]  # Asumsi kolom pertama adalah PK
                
                record_options = df[primary_key_col].tolist()
                selected_record = st.selectbox(
                    f"Pilih {primary_key_col} untuk di-update",
                    record_options
                )
                
                if selected_record is not None:
                    # Dapatkan data record yang dipilih
                    current_data = df[df[primary_key_col] == selected_record].iloc[0]
                    
                    st.markdown("**Data Saat Ini:**")
                    st.json(current_data.to_dict())
                    
                    st.markdown("---")
                    st.markdown("**Form Update:**")
                    
                    # Form untuk update
                    updates = {}
                    schema = get_table_schema(selected_table)
                    
                    for col in schema:
                        col_id, col_name, col_type, not_null, default_val, is_pk = col
                        
                        # Skip primary key
                        if is_pk:
                            continue
                        
                        current_value = current_data[col_name]
                        
                        # Input field
                        if col_type.upper() in ["INTEGER", "NUMERIC"]:
                            updates[col_name] = st.number_input(
                                f"{col_name}",
                                value=float(current_value) if pd.notna(current_value) else 0.0,
                                key=f"update_{col_name}"
                            )
                        elif col_type.upper() == "BOOLEAN":
                            updates[col_name] = st.checkbox(
                                f"{col_name}",
                                value=bool(current_value) if pd.notna(current_value) else False,
                                key=f"update_{col_name}"
                            )
                        else:
                            updates[col_name] = st.text_area(
                                f"{col_name}",
                                value=str(current_value) if pd.notna(current_value) else "",
                                key=f"update_{col_name}",
                                height=100 if col_type.upper() in ["TEXT", "JSON"] else 50
                            )
                    
                    if st.button("✏️ Update Data", type="primary"):
                        try:
                            affected = update_record(selected_table, primary_key_col, selected_record, updates)
                            st.success(f"✅ Data berhasil diupdate! ({affected} baris terpengaruh)")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
            else:
                st.info("Tabel kosong")
        
        # TAB 4: DELETE
        with tab4:
            st.subheader(f"Hapus Data dari: {selected_table}")
            st.warning("⚠️ Hati-hati! Operasi ini tidak bisa di-undo!")
            
            # Dapatkan data
            df = get_table_data(selected_table, 100)
            
            if not df.empty:
                # Pilih record untuk dihapus
                primary_key_col = df.columns[0]
                
                st.dataframe(df, use_container_width=True)
                
                st.markdown("---")
                
                record_options = df[primary_key_col].tolist()
                selected_record = st.selectbox(
                    f"Pilih {primary_key_col} untuk dihapus",
                    record_options,
                    key="delete_select"
                )
                
                if selected_record is not None:
                    # Tampilkan data yang akan dihapus
                    record_to_delete = df[df[primary_key_col] == selected_record].iloc[0]
                    
                    st.markdown("**Data yang akan dihapus:**")
                    st.json(record_to_delete.to_dict())
                    
                    # Konfirmasi
                    confirm = st.checkbox("Saya yakin ingin menghapus data ini")
                    
                    if confirm:
                        if st.button("🗑️ Hapus Data", type="primary"):
                            try:
                                affected = delete_record(selected_table, primary_key_col, selected_record)
                                st.success(f"✅ Data berhasil dihapus! ({affected} baris terhapus)")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
            else:
                st.info("Tabel kosong")

# ==================== MODE: JSON Files ====================
elif mode == "JSON Files":
    st.header("📄 JSON Files Manager")
    
    # Dapatkan daftar file JSON
    json_files = get_json_files()
    
    if not json_files:
        st.warning(f"Tidak ada file JSON di folder: {JSON_DIR}")
    else:
        # Tabs
        tab1, tab2, tab3 = st.tabs(["📖 View", "✏️ Edit", "🗑️ Delete"])
        
        # TAB 1: VIEW
        with tab1:
            st.subheader("Lihat File JSON")
            
            selected_file = st.selectbox("Pilih File", json_files, key="view_json")
            
            if selected_file:
                try:
                    data = read_json_file(selected_file)
                    
                    st.markdown(f"**File:** `{selected_file}`")
                    st.markdown(f"**Path:** `{JSON_DIR / selected_file}`")
                    
                    # Tampilkan sebagai JSON
                    st.json(data)
                    
                    # Download
                    json_str = json.dumps(data, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_str,
                        file_name=selected_file,
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"❌ Error membaca file: {str(e)}")
        
        # TAB 2: EDIT
        with tab2:
            st.subheader("Edit File JSON")
            
            selected_file = st.selectbox("Pilih File", json_files, key="edit_json")
            
            if selected_file:
                try:
                    data = read_json_file(selected_file)
                    
                    st.markdown(f"**File:** `{selected_file}`")
                    
                    # Editor
                    json_str = json.dumps(data, indent=2, ensure_ascii=False)
                    edited_json = st.text_area(
                        "Edit JSON (format harus valid)",
                        value=json_str,
                        height=400
                    )
                    
                    if st.button("💾 Simpan Perubahan", type="primary"):
                        try:
                            # Validasi JSON
                            new_data = json.loads(edited_json)
                            
                            # Simpan
                            write_json_file(selected_file, new_data)
                            st.success("✅ File berhasil disimpan!")
                            st.rerun()
                        except json.JSONDecodeError as e:
                            st.error(f"❌ JSON tidak valid: {str(e)}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error membaca file: {str(e)}")
        
        # TAB 3: DELETE
        with tab3:
            st.subheader("Hapus File JSON")
            st.warning("⚠️ Hati-hati! File yang dihapus tidak bisa dikembalikan!")
            
            selected_file = st.selectbox("Pilih File", json_files, key="delete_json")
            
            if selected_file:
                try:
                    data = read_json_file(selected_file)
                    
                    st.markdown(f"**File yang akan dihapus:** `{selected_file}`")
                    st.json(data)
                    
                    # Konfirmasi
                    confirm = st.checkbox("Saya yakin ingin menghapus file ini")
                    
                    if confirm:
                        if st.button("🗑️ Hapus File", type="primary"):
                            try:
                                delete_json_file(selected_file)
                                st.success("✅ File berhasil dihapus!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error membaca file: {str(e)}")

# Footer
st.markdown("---")
st.caption(f"Database: {DB_PATH} | JSON Directory: {JSON_DIR}")
