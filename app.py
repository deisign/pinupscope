import json
import os
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from telegram import Bot

# Настройки
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = st.secrets["google"]["folder_id"]

# Авторизация Google Drive через консольный поток
def authenticate_google_drive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        
        # Генерация ссылки авторизации
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        # Вывод ссылки в интерфейсе Streamlit
        st.write("Перейдите по следующей ссылке для авторизации Google Drive:")
        st.write(auth_url)
        
        # Ввод кода авторизации вручную
        auth_code = st.text_input("Введите код авторизации:")
        if auth_code:
            try:
                flow.fetch_token(code=auth_code)
                creds = flow.credentials

                # Сохранение токена
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                st.error(f"Ошибка авторизации: {e}")
    return creds

# Получение списка файлов из папки Google Drive
def list_files_in_folder(folder_id):
    try:
        creds = authenticate_google_drive()
        if not creds:
            return []
        service = build('drive', 'v3', credentials=creds)
        query = f"'{folder_id}' in parents and mimeType='image/jpeg'"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        return results.get('files', [])
    except HttpError as error:
        st.error(f"Произошла ошибка: {error}")
        return []

# Публикация изображения в Telegram
def post_to_telegram(file_name, file_url):
    try:
        bot = Bot(token=st.secrets["telegram"]["token"])
        bot.send_photo(chat_id=st.secrets["telegram"]["channel"], photo=file_url, caption=f"🎨 {file_name}")
        st.success(f"Изображение {file_name} опубликовано!")
    except Exception as e:
        st.error(f"Ошибка при отправке: {e}")

# Интерфейс Streamlit
st.title("Пинап-постер в Telegram")

# Показ списка файлов в папке Google Drive
if FOLDER_ID:
    files = list_files_in_folder(FOLDER_ID)
    if files:
        st.write("Доступные файлы:")
        for file in files:
            file_name = file['name']
            file_id = file['id']
            file_url = f"https://drive.google.com/uc?id={file_id}"
            st.write(f"**{file_name}**")
            if st.button(f"Опубликовать {file_name}"):
                post_to_telegram(file_name, file_url)
    else:
        st.warning("Файлы не найдены в указанной папке.")
else:
    st.error("Не указан идентификатор папки Google Диска.")
