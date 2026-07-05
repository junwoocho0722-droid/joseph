        """학교 보건실 재고 관리 앱.

이 Streamlit 앱은 학교 보건실 물품 재고 관리만을 위한 앱입니다.
의학적 조언이나 의약품 추천을 제공하지 않으며, 학생 이름, 증상, 질병,
개인 건강 정보는 저장하지 않습니다.
"""

from datetime import date, datetime
import hmac
import os
import sqlite3

import pandas as pd
import streamlit as st


DB_FILE = "health_room_inventory.db"
CATEGORIES = [
    "의약품",
    "응급처치 용품",
    "위생용품",
    "소독용품",
    "기타",
]
INVENTORY_COLUMNS_KO = {
    "id": "번호",
    "item_name": "물품명",
    "category": "분류",
    "current_quantity": "현재 수량",
    "minimum_quantity": "최소 수량",
    "expiration_date": "유효기간",
    "storage_location": "보관 위치",
    "notes": "메모",
}
USAGE_COLUMNS_KO = {
    "id": "기록 번호",
    "item_id": "물품 번호",
    "item_name": "물품명",
    "used_date": "사용 날짜",
    "quantity_used": "사용 수량",
}


def get_app_password():
    """Streamlit secrets 또는 환경 변수에서 접속 비밀번호를 가져옵니다."""
    try:
        return st.secrets.get("APP_PASSWORD", "")
    except Exception:
        return os.environ.get("APP_PASSWORD", "")


def check_password():
    """간단한 비밀번호 확인 화면을 보여줍니다."""
    app_password = get_app_password()

    if not app_password:
        st.warning(
            "접속 비밀번호가 설정되지 않았습니다. 인터넷에 배포할 때는 "
            "반드시 APP_PASSWORD를 설정하세요."
        )
        return True

    if st.session_state.get("password_correct"):
        return True

    st.title("학교 보건실 재고 관리")
    st.info("접속 비밀번호를 입력하세요.")
    password = st.text_input("비밀번호", type="password")

    if st.button("접속"):
        if hmac.compare_digest(password, app_password):
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("비밀번호가 맞지 않습니다.")

    return False


def get_connection():
    """로컬 SQLite 데이터베이스 파일에 연결합니다."""
    return sqlite3.connect(DB_FILE)


def setup_database():
    """데이터베이스 표가 없으면 새로 만듭니다."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                category TEXT NOT NULL,
                current_quantity INTEGER NOT NULL,
                minimum_quantity INTEGER NOT NULL,
                expiration_date TEXT NOT NULL,
                storage_location TEXT NOT NULL,
                notes TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                used_date TEXT NOT NULL,
                quantity_used INTEGER NOT NULL,
                FOREIGN KEY (item_id) REFERENCES inventory (id)
            )
            """
        )
        conn.commit()


def load_inventory():
    """모든 재고 물품을 pandas DataFrame으로 읽어옵니다."""
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM inventory ORDER BY item_name",
            conn,
            parse_dates=["expiration_date"],
        )


def load_usage_log():
    """사용 기록을 읽고 표시용 물품명을 함께 가져옵니다."""
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT
                usage_log.id,
                usage_log.item_id,
                inventory.item_name,
                usage_log.used_date,
                usage_log.quantity_used
            FROM usage_log
            JOIN inventory ON usage_log.item_id = inventory.id
            ORDER BY usage_log.used_date DESC, usage_log.id DESC
            """,
            conn,
            parse_dates=["used_date"],
        )


def add_inventory_item(
    item_name,
    category,
    current_quantity,
    minimum_quantity,
    expiration_date,
    storage_location,
    notes,
):
    """새 재고 물품을 저장합니다."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO inventory (
                item_name,
                category,
                current_quantity,
                minimum_quantity,
                expiration_date,
                storage_location,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_name,
                category,
                current_quantity,
                minimum_quantity,
                expiration_date.isoformat(),
                storage_location,
                notes,
            ),
        )
        conn.commit()


def update_item_quantity(item_id, new_quantity):
    """한 물품의 현재 재고 수량을 수정합니다."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE inventory SET current_quantity = ? WHERE id = ?",
            (new_quantity, item_id),
        )
        conn.commit()


def record_usage(item_id, used_date, quantity_used):
    """재고 사용 기록을 저장합니다.

    사용 기록에는 물품, 날짜, 수량만 저장합니다. 학생 이름, 증상, 질병,
    개인 건강 정보는 저장하지 않습니다.
    """
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO usage_log (item_id, used_date, quantity_used)
            VALUES (?, ?, ?)
            """,
            (item_id, used_date.isoformat(), quantity_used),
        )
        conn.commit()


def make_download(df):
    """다운로드 버튼에 사용할 CSV 데이터를 만듭니다."""
    return df.to_csv(index=False).encode("utf-8")


def rename_columns_to_korean(df, column_map):
    """표와 CSV에서 보이도록 열 이름을 한국어로 바꿉니다."""
    return df.rename(columns=column_map)


def show_safety_notice():
    """재고 관리 전용 안전 안내문을 보여줍니다."""
    st.info(
        "재고 관리 전용 도구입니다. 학생 이름, 증상, 질병, 개인 건강 정보를 "
        "입력하지 마세요. 이 앱은 의학적 조언을 제공하거나 의약품을 추천하지 않습니다."
    )


def show_dashboard(inventory, usage_log):
    """요약 숫자, 알림, 이달의 사용량 상위 물품을 보여줍니다."""
    st.header("재고 현황판")

    today = pd.Timestamp(date.today())
    next_30_days = today + pd.Timedelta(days=30)

    low_stock = inventory[
        inventory["current_quantity"] <= inventory["minimum_quantity"]
    ]
    expiring_soon = inventory[
        (inventory["expiration_date"] >= today)
        & (inventory["expiration_date"] <= next_30_days)
    ]
    expired = inventory[inventory["expiration_date"] < today]

    total_items = len(inventory)
    total_low_stock = len(low_stock)
    total_expiring = len(expiring_soon)
    total_expired = len(expired)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("전체 물품 수", total_items)
    col2.metric("부족 물품", total_low_stock)
    col3.metric("30일 이내 유효기간", total_expiring)
    col4.metric("유효기간 지남", total_expired)

    st.subheader("이달의 사용량 상위 물품")
    if usage_log.empty:
        st.write("아직 사용 기록이 없습니다.")
    else:
        first_day = pd.Timestamp(date.today().replace(day=1))
        this_month = usage_log[usage_log["used_date"] >= first_day]
        if this_month.empty:
            st.write("이번 달 사용 기록이 없습니다.")
        else:
            top_used = (
                this_month.groupby("item_name", as_index=False)["quantity_used"]
                .sum()
                .sort_values("quantity_used", ascending=False)
                .head(10)
            )
            top_used = rename_columns_to_korean(top_used, USAGE_COLUMNS_KO)
            st.dataframe(top_used, use_container_width=True, hide_index=True)

    st.subheader("전체 재고")
    st.dataframe(
        rename_columns_to_korean(inventory, INVENTORY_COLUMNS_KO),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("알림")
    if low_stock.empty:
        st.success("부족한 물품이 없습니다.")
    else:
        st.warning("재고가 부족한 물품을 확인하세요.")
        st.dataframe(
            rename_columns_to_korean(
                low_stock[
                    [
                        "item_name",
                        "category",
                        "current_quantity",
                        "minimum_quantity",
                        "storage_location",
                    ]
                ],
                INVENTORY_COLUMNS_KO,
            ),
            use_container_width=True,
            hide_index=True,
        )

    if expiring_soon.empty:
        st.success("30일 이내에 유효기간이 끝나는 물품이 없습니다.")
    else:
        st.warning("30일 이내에 유효기간이 끝나는 물품을 확인하세요.")
        st.dataframe(
            rename_columns_to_korean(
                expiring_soon[
                    [
                        "item_name",
                        "category",
                        "current_quantity",
                        "expiration_date",
                        "storage_location",
                    ]
                ],
                INVENTORY_COLUMNS_KO,
            ),
            use_container_width=True,
            hide_index=True,
        )

    if not expired.empty:
        st.error("유효기간이 지난 물품입니다. 재고 점검이 필요합니다.")
        st.dataframe(
            rename_columns_to_korean(
                expired[
                    [
                        "item_name",
                        "category",
                        "current_quantity",
                        "expiration_date",
                        "storage_location",
                    ]
                ],
                INVENTORY_COLUMNS_KO,
            ),
            use_container_width=True,
            hide_index=True,
        )


def show_add_item_form():
    """새 재고 물품을 추가하는 입력 양식을 보여줍니다."""
    st.header("재고 물품 추가")
    with st.form("add_item_form", clear_on_submit=True):
        item_name = st.text_input("물품명")
        category = st.selectbox("분류", CATEGORIES)
        current_quantity = st.number_input("현재 수량", min_value=0, step=1)
        minimum_quantity = st.number_input("최소 수량", min_value=0, step=1)
        expiration_date = st.date_input("유효기간", min_value=date(2000, 1, 1))
        storage_location = st.text_input("보관 위치")
        notes = st.text_area(
            "메모",
            placeholder="재고 관련 메모만 입력하세요. 학생 정보나 건강 정보는 입력하지 마세요.",
        )

        submitted = st.form_submit_button("물품 추가")

    if submitted:
        if not item_name.strip() or not storage_location.strip():
            st.error("물품명과 보관 위치를 모두 입력하세요.")
            return

        add_inventory_item(
            item_name.strip(),
            category,
            int(current_quantity),
            int(minimum_quantity),
            expiration_date,
            storage_location.strip(),
            notes.strip(),
        )
        st.success("재고 물품이 추가되었습니다.")
        st.rerun()


def choose_item(inventory, label):
    """물품을 선택하게 하고 선택된 행을 돌려줍니다."""
    item_options = {
        f"{row.item_name} | 재고: {row.current_quantity} | 위치: {row.storage_location}": row
        for row in inventory.itertuples()
    }
    selected_label = st.selectbox(label, list(item_options.keys()))
    return item_options[selected_label]


def show_use_item_form(inventory):
    """사용한 수량만큼 재고를 차감하는 입력 양식을 보여줍니다."""
    st.header("물품 사용")
    st.caption("재고 사용량만 기록하세요. 학생 정보나 건강 정보는 입력하지 마세요.")

    if inventory.empty:
        st.write("먼저 재고 물품을 추가하세요.")
        return

    selected_item = choose_item(inventory, "물품 선택")

    with st.form("use_item_form"):
        quantity_used = st.number_input(
            "사용 수량",
            min_value=1,
            max_value=max(1, int(selected_item.current_quantity)),
            step=1,
        )
        used_date = st.date_input("사용 날짜", value=date.today())
        submitted = st.form_submit_button("사용 기록")

    if submitted:
        if quantity_used > selected_item.current_quantity:
            st.error("사용 수량은 현재 재고보다 많을 수 없습니다.")
            return

        new_quantity = int(selected_item.current_quantity) - int(quantity_used)
        update_item_quantity(int(selected_item.id), new_quantity)
        record_usage(int(selected_item.id), used_date, int(quantity_used))
        st.success("재고가 수정되고 사용 기록이 저장되었습니다.")
        st.rerun()


def show_add_stock_form(inventory):
    """기존 물품에 재고를 추가하는 입력 양식을 보여줍니다."""
    st.header("재고 추가")

    if inventory.empty:
        st.write("먼저 재고 물품을 추가하세요.")
        return

    selected_item = choose_item(inventory, "물품 선택")

    with st.form("add_stock_form"):
        quantity_added = st.number_input("추가 수량", min_value=1, step=1)
        submitted = st.form_submit_button("재고 추가")

    if submitted:
        new_quantity = int(selected_item.current_quantity) + int(quantity_added)
        update_item_quantity(int(selected_item.id), new_quantity)
        st.success("재고가 추가되었습니다.")
        st.rerun()


def show_exports(inventory, usage_log):
    """재고와 사용 기록을 CSV로 다운로드하는 버튼을 보여줍니다."""
    st.header("데이터 내보내기")
    st.download_button(
        "재고 CSV 다운로드",
        data=make_download(rename_columns_to_korean(inventory, INVENTORY_COLUMNS_KO)),
        file_name=f"inventory_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
    st.download_button(
        "사용 기록 CSV 다운로드",
        data=make_download(rename_columns_to_korean(usage_log, USAGE_COLUMNS_KO)),
        file_name=f"usage_log_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )


def main():
    """Streamlit 앱을 실행합니다."""
    st.set_page_config(
        page_title="학교 보건실 재고 관리",
        page_icon=":package:",
        layout="wide",
    )

    if not check_password():
        return

    setup_database()

    st.title("학교 보건실 재고 관리")
    show_safety_notice()

    inventory = load_inventory()
    usage_log = load_usage_log()

    pages = [
        "현황판",
        "재고 물품 추가",
        "물품 사용",
        "재고 추가",
        "데이터 내보내기",
    ]
    selected_page = st.sidebar.radio("메뉴", pages)

    if selected_page == "현황판":
        show_dashboard(inventory, usage_log)
    elif selected_page == "재고 물품 추가":
        show_add_item_form()
    elif selected_page == "물품 사용":
        show_use_item_form(inventory)
    elif selected_page == "재고 추가":
        show_add_stock_form(inventory)
    elif selected_page == "데이터 내보내기":
        show_exports(inventory, usage_log)


if __name__ == "__main__":
    main()

        add_inventory_item(
            item_name.strip(),
            category,
            int(current_quantity),
            int(minimum_quantity),
            expiration_date,
            storage_location.strip(),
            notes.strip(),
        )
        st.success("재고 물품이 추가되었습니다.")
        st.rerun()


def choose_item(inventory, label):
    """물품을 선택하게 하고 선택된 행을 돌려줍니다."""
    item_options = {
        f"{row.item_name} | 재고: {row.current_quantity} | 위치: {row.storage_location}": row
        for row in inventory.itertuples()
    }
    selected_label = st.selectbox(label, list(item_options.keys()))
    return item_options[selected_label]


def show_use_item_form(inventory):
    """사용한 수량만큼 재고를 차감하는 입력 양식을 보여줍니다."""
    st.header("물품 사용")
    st.caption("재고 사용량만 기록하세요. 학생 정보나 건강 정보는 입력하지 마세요.")

    if inventory.empty:
        st.write("먼저 재고 물품을 추가하세요.")
        return

    selected_item = choose_item(inventory, "물품 선택")

    with st.form("use_item_form"):
        quantity_used = st.number_input(
            "사용 수량",
            min_value=1,
            max_value=max(1, int(selected_item.current_quantity)),
            step=1,
        )
        used_date = st.date_input("사용 날짜", value=date.today())
        submitted = st.form_submit_button("사용 기록")

    if submitted:
        if quantity_used > selected_item.current_quantity:
            st.error("사용 수량은 현재 재고보다 많을 수 없습니다.")
            return

        new_quantity = int(selected_item.current_quantity) - int(quantity_used)
        update_item_quantity(int(selected_item.id), new_quantity)
        record_usage(int(selected_item.id), used_date, int(quantity_used))
        st.success("재고가 수정되고 사용 기록이 저장되었습니다.")
        st.rerun()


def show_add_stock_form(inventory):
    """기존 물품에 재고를 추가하는 입력 양식을 보여줍니다."""
    st.header("재고 추가")

    if inventory.empty:
        st.write("먼저 재고 물품을 추가하세요.")
        return

    selected_item = choose_item(inventory, "물품 선택")

    with st.form("add_stock_form"):
        quantity_added = st.number_input("추가 수량", min_value=1, step=1)
        submitted = st.form_submit_button("재고 추가")

    if submitted:
        new_quantity = int(selected_item.current_quantity) + int(quantity_added)
        update_item_quantity(int(selected_item.id), new_quantity)
        st.success("재고가 추가되었습니다.")
        st.rerun()


def show_exports(inventory, usage_log):
    """재고와 사용 기록을 CSV로 다운로드하는 버튼을 보여줍니다."""
    st.header("데이터 내보내기")
    st.download_button(
        "재고 CSV 다운로드",
        data=make_download(rename_columns_to_korean(inventory, INVENTORY_COLUMNS_KO)),
        file_name=f"inventory_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
    st.download_button(
        "사용 기록 CSV 다운로드",
        data=make_download(rename_columns_to_korean(usage_log, USAGE_COLUMNS_KO)),
        file_name=f"usage_log_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )


def main():
    """Streamlit 앱을 실행합니다."""
    st.set_page_config(
        page_title="학교 보건실 재고 관리",
        page_icon=":package:",
        layout="wide",
    )

    if not check_password():
        return

    setup_database()

    st.title("학교 보건실 재고 관리")
    show_safety_notice()

    inventory = load_inventory()
    usage_log = load_usage_log()

    pages = [
        "현황판",
        "재고 물품 추가",
        "물품 사용",
        "재고 추가",
        "데이터 내보내기",
    ]
    selected_page = st.sidebar.radio("메뉴", pages)

    if selected_page == "현황판":
        show_dashboard(inventory, usage_log)
    elif selected_page == "재고 물품 추가":
        show_add_item_form()
    elif selected_page == "물품 사용":
        show_use_item_form(inventory)
    elif selected_page == "재고 추가":
        show_add_stock_form(inventory)
    elif selected_page == "데이터 내보내기":
        show_exports(inventory, usage_log)


if __name__ == "__main__":
    main()
