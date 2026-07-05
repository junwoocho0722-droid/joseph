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
