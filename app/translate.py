from hashlib import md5
import random
import requests
from app import app
from flask_babel import _


def translate(text, source_language, dest_language):
    if 'BAIDU_TRANSLATOR_ID' not in app.config or 'BAIDU_TRANSLATOR_KEY' not in app.config or\
            not app.config['BAIDU_TRANSLATOR_ID'] or not app.config['BAIDU_TRANSLATOR_KEY']:
        return _('Error: the translation service is not configured.')
    
    salt = random.randint(32768, 65536)
    translator_id = app.config['BAIDU_TRANSLATOR_ID']
    translator_key = app.config['BAIDU_TRANSLATOR_KEY']
    signed_str = md5('{}{}{}{}'.format(translator_id, text, salt, translator_key).encode()).hexdigest()
    url = 'http://api.fanyi.baidu.com/api/trans/vip/translate?q={}&from={}&to={}&appid={}&salt={}&sign={}'.format(
        text, source_language, dest_language, translator_id, salt, signed_str
    )
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json().get('trans_result')[0].get('dst')
    return text