import streamlit as st
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd

st.title("Парсер товаров из чека")
st.write("Введите ссылку на чек:")

link = st.text_input("Ссылка")

if link:
    try:
        # Парсинг данных
        receipe_response = requests.get(link)
        receipe_response.encoding = 'utf-8'
        receipe_soup = BeautifulSoup(receipe_response.text, 'lxml')

        items = receipe_soup.find('table', class_='receipt-body').find_all('div', class_='item')
        
        items_list = []
        for i in items:
            item = i.find('span', class_='value receipt-value-1030').text
            item = re.sub('; кг', '', re.sub('; шт.', '', re.sub('\r\n', '', item))).strip()
            price = i.find('span', class_='value receipt-value-1079').text
            amount = i.find('span', class_='value receipt-value-1023').text
            full_price = i.find('span', class_='value receipt-value-1043').text

            item_dict = {
                'Наименование': item,
                'Цена за шт': float(price),
                'Кол-во': float(amount),
                'Стоимость': float(full_price),
                'Доля': 0.0  # Добавляем колонку для редактирования
            }
            items_list.append(item_dict)

        df = pd.DataFrame(items_list)

        # Редактируемая таблица
        st.subheader("Редактируйте доли (0-1):")
        edited_df = st.data_editor(
            df,
            column_config={
                "Доля": st.column_config.NumberColumn(
                    min_value=0.0,
                    max_value=1.0,
                    step=0.01,
                    format="%.2f"
                )
            },
            disabled=["Наименование", "Цена за шт", "Кол-во", "Стоимость"],
            hide_index=True
        )

        # Обновляем метрики на основе edited_df
        m1, m2 = st.columns((1, 1))
        m1.metric(label='Сумма чека', value=round(sum(edited_df['Стоимость']), 2))
        m2.metric(
            label='Ваша часть', 
            value=round(sum(edited_df['Стоимость'] * edited_df['Доля']), 2)
        )

        # Кнопка для скачивания Excel
        st.download_button(
            label="Скачать Excel",
            data=edited_df.to_csv(index=False, sep=';').encode('utf-8'),
            file_name='receipt_data.csv',
            mime='text/csv'
        )
        
    except Exception as e:
        st.error(f"Ошибка: {e}")