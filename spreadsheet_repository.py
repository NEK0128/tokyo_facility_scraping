from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

class SpreadsheetRepository():
    SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
    APPLICATION_NAME = 'Tennis Reservation'
    DISCOVERY_URL = 'https://sheets.googleapis.com/$discovery/rest?version=v4'

    def __init__(self, credential_path, client_secret_file=None, args=None):
        # 認証情報取得してシートにアクセスする準備
        credentials = self._get_credentials(credential_path, client_secret_file, args)
        service = discovery.build(
            'sheets',
            'v4',
            http=credentials.authorize(httplib2.Http()),
            discoveryServiceUrl=SpreadsheetRepository.DISCOVERY_URL
        )
        self.sheets = service.spreadsheets()

    def update(self, sheet_id, range_name, body):
        """シートを更新する
        """
        result = self.sheets.values().update(
            spreadsheetId=sheet_id, range=range_name,
            valueInputOption="RAW",
            body=body).execute()

    def get(self, sheet_id, range_name):
        """シートの情報を得る
        """
        result = self.sheets.values().get(
            spreadsheetId=sheet_id, range=range_name).execute()
        return result.get('values', [])


    def _get_credentials(self, credential_path, client_secret_file=None, flags=None):
        """認証情報を取得します。
        認証情報がない/有効でない場合は新たに認証を作ります。
        """
        # 指定したパスに認証情報があるか確認
        os.makedirs(os.path.dirname(credential_path), exist_ok=True)
        store = Storage(credential_path)
        credentials = store.get()

        # 認証情報がない場合は作成
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(
                client_secret_file,
                SpreadsheetRepository.SCOPES
            )
            flow.user_agent = SpreadsheetRepository.APPLICATION_NAME
            credentials = tools.run_flow(flow, store, flags)
            print('Storing credentials to ' + credential_path)
        return credentials


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    parser.add_argument('credential_path')
    parser.add_argument('client_secret_path', nargs='?', default=None)
    args = parser.parse_args()

    repository = SpreadsheetRepository(
        args.credential_path,
        args.client_secret_path ,
        args)

    print(repository.get(
        '1okZajm209ROu2a55xpvGApor5ErzxIlBdT4bBir1HvQ',
        'empty_info!A2:A3'))
