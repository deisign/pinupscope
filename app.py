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
TELEGRAM_TOKEN = "7917872223:AAH6U7E3KRs5rg6Tq1QixK1_tgEN1dcEN0o"
TELEGRAM_CHANNEL = "@pinupscope"
FOLDER_ID = "1duGXZE6iUp1px9pNqYTxjd2WIDsBYWsH"

# Чтение данных из Streamlit Secrets и создание `credentials.json`
def create_credentials_file():
    creds_data = {
        "installed": {
            "client_id": st.secrets["google_credentials"]["client_id"],
            "project_id": st.secrets["google_credentials"]["project_id"],
            "auth_uri": st.secrets["google_credentials"]["auth_uri"],
            "token_uri": st.secrets["google_credentials"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google_credentials"]["auth_provider_x509_cert_url"],
            "client_secret": st.secrets["google_credentials"]["client_secret"],
            "redirect_uris": [st.secrets["google_credentials"]["redirect_uris"]]
        }
    }
    with open("credentials.json", "w") as creds_file:
        json.dump(creds_data, creds_file)

# Авторизация Google Drive
def authenticate_google_drive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# Получение списка файлов из папки Google Drive
def list_files_in_folder(folder_id):
    try:
        creds = authenticate_google_drive()
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
        bot = Bot(token=TELEGRAM_TOKEN)
        bot.send_photo(chat_id=TELEGRAM_CHANNEL, photo=file_url, caption=f"🎨 {file_name}")
        st.success(f"Изображение {file_name} опубликовано!")
    except Exception as e:
        st.error(f"Ошибка при отправке: {e}")

# Интерфейс Streamlit
st.title("Пинап-постер в Telegram")

# Подготовка `credentials.json` из Streamlit Secrets
create_credentials_file()

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

