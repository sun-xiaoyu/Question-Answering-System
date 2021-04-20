import paramiko
import json
import re
import wikipedia as wiki
import requests
import logging

from wikipedia.exceptions import DisambiguationError

logging.basicConfig(
    format='%(asctime)s %(levelname)s  %(name)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)


requests.adapters.DEFAULT_RETRIES = 5

# 将sshclient的对象的transport指定为以上的trans

# 执行命令，和传统方法一样
# stdin, stdout, stderr = ssh.exec_command('ls')
# print(stdout.read().decode())

# todo important use this line to open ssl port forwarding:
'''
ssh -L localhost:5667:localhost:5666 sunxy-s18@10.134.171.215 -p 2222
'''

_SPECIAL_TOKENS_RE = re.compile(r"^\[[^ ]*\]$", re.UNICODE)
tags_to_keep = ["<Table>", "<P>", "<Ul>", "<Dl>", "<Ol>", "<Tr>", "<Li>", "<Dd>", "<Dt>"]
_HTML_TOKENS_RE = re.compile(r"^<[^ ]*>$", re.UNICODE)
_HTML_TAGS_RE = re.compile(r"<[^>]*>", re.UNICODE)


def get_wiki_page(question):
    related_entries = wiki.search(question)
    if len(related_entries) > 0:
        page = wiki.page(related_entries[0])
        return page
    else:
        return None

def clean_html(html):
    html = _SPECIAL_TOKENS_RE.sub(' ', html)
    html = re.sub('<p>', '[Paragraph] ', html)
    html = re.sub('<Table>', '[Table] ', html)
    html = re.sub('<Ul>', '[List] ', html)
    html = re.sub('<Dl>', '[List] ', html)
    html = re.sub('<Ol>', '[List] ', html)
    html = re.sub('<h2>', '[h2] ', html)
    html = _HTML_TAGS_RE.sub(' ', html)
    html = re.sub('-', ' - ', html)
    html = re.sub(r"\'", "'", html)
    html = re.sub(r'&#91;\d+&#93;', ' ', html)
    html = re.sub(r'&#\d*;', ' ', html)
    html = re.sub('([.,!?()])', r' \1 ', html)
    html = re.sub('\s{2,}', ' ', html)
    html = re.sub(r'\[ edit \]', ' ', html)
    return html



def find_long_ans(span, html):
    # special_token_pos = _SPECIAL_TOKENS_RE.finditer(html)
    html_tokens = html.split(' ')
    special_token_pos = [i for i, token in enumerate(html_tokens) if _SPECIAL_TOKENS_RE.match(token)]
    for i in range(1, len(special_token_pos)):
        if special_token_pos[i-1] <= span[0] and special_token_pos[i] >= span[1]:
            la = special_token_pos[i-1], special_token_pos[i] - 1
            long_ans = ' '.join(html_tokens[la[0]: la[1] + 1])
            return long_ans, la
    return "N/A. Can't map back to a long answer.", (-1,-1)



def post_process(js, html):
    # js = json.loads(raw_output)
    ans = js['answer']
    answerability_probs = ans['answer_type_probs'][:3]
    answerability_probs = [round(x, 4) for x in answerability_probs]
    sa_span = ans['best_span_orig']
    short_ans = ans['best_span_str']
    if short_ans == '':
        short_ans = long_ans = "No answer found on the page."
        yn_probs = None
        return short_ans, long_ans, answerability_probs, yn_probs

    long_ans, la_span = find_long_ans(sa_span, html)
    # yn_probs = '1 1 1'
    # yn_ans = 'NONE'
    yn_ans = ans['yn_ans']
    yn_probs = ans['yn_probs'][2:]
    yn_probs = [round(x, 4) for x in yn_probs]
    if yn_ans != 'NONE':
        short_ans = yn_ans
    if la_span[0] == sa_span[0] - 1 and la_span[1] == sa_span[1]:
        short_ans = "No short answer."

    return short_ans, long_ans, answerability_probs, yn_probs



class QAsystem(object):
    def __init__(self):
        trans = paramiko.Transport(('10.134.171.215', 2222))
        # 建立连接
        trans.connect(username='sunxy-s18', password='xiaoyu123')
        ssh = paramiko.SSHClient()
        ssh._transport = trans
        sftp = paramiko.SFTPClient.from_transport(trans)
        # 发送文件

        self.ssh = ssh
        self.trans = trans
        self.sftp = sftp
        # use text or html
        # self.use_text = True
        self.use_text = False
        logging.info(f'We only use text on the wikipedia page: {self.use_text}')

    def __del__(self):
        self.trans.close()

    def ask(self, question: str = "Why is the sky blue?", reference_url=None):
        # prefix = '''curl -X POST --header "Content-Type: application/json" --data \''''
        # postfix = '''\' 127.0.0.1:5666/predict'''
        # prefixf = '''curl -X POST --header "Content-Type: application/json" --data @'''
        # postfixf = ''' 127.0.0.1:5666/predict'''
        logger.info(f'Reference: {reference_url}')
        logger.info(question)
        if reference_url is not None:
            if 'http' in reference_url or 'wikipedia' in reference_url:
                r = requests.get(reference_url)
                html = r.text
                with open('user_defined_html.log', 'w+', encoding='utf-8') as f:
                    f.write(question + '\n')
                    f.write(html + '\n'*5+'{{{sep}}}'+'\n'*5)
                cleaned_html = clean_html(html)
                print("here1")
                d = re.search('<\W*title\W*(.*)</title', html, re.IGNORECASE)
                try:
                    title = d.group(1)
                except:
                    title = ''
                    logger.info('title not found')
                url = reference_url
            else:
                # input is a title
                try:
                    page = wiki.page(reference_url)
                    print("here2")
                except DisambiguationError as e:
                    return f'Your question is ambiguous.\n{e.title} may refer to: {e.options}'
                if not page:
                    return 'No related Wikipedia pages are found.\n You may consider another question or refer to an example on the home page.'
                # html = '<html><\html><html><\html><html><\html><html><\html>'
                # todo
                if self.use_text:
                    cleaned_html = page.content
                else:
                    html = page.html()
                    cleaned_html = clean_html(html)
                title = page.title
                url = page.url
        else:
            try:
                page = get_wiki_page(question)
                print("here3")
            except DisambiguationError as e:
                return f'Your question is ambiguous.\n{e.title} may refer to: {e.options}'
            if not page:
                return 'No related Wikipedia pages are found.\n ' \
                       'You may consider another question or refer to an example on the home page.'
            # html = '<html><\html><html><\html><html><\html><html><\html>'
            # todo
            if self.use_text:
                cleaned_html = page.content
            else:
                html = page.html()
                cleaned_html = clean_html(html)
            title = page.title
            url = page.url
        js = {
            "question": question,
            "html": cleaned_html,
        }
        logger.info(cleaned_html[:50])
        # js_str = json.dumps(js, ensure_ascii=False)
        # with open('D://body.json', 'w', encoding='utf-8') as f:
        #     f.write(js_str)
        # remotepath = '/home/sunxy-s18/data/demo/body.json'
        # self.sftp.put(localpath='D://body.json', remotepath=remotepath)
        # print(js_str)
        # # cmd = prefix + js_str + postfix
        # cmdf = prefixf + remotepath + postfixf
        # print(cmdf)
        # stdin, stdout, stderr = self.ssh.exec_command(cmdf)
        # raw_output = stdout.read().decode()
        returned = requests.post('http://localhost:5667/predict', json=js)
        returned_js = returned.json()
        # logger.info(returned_js)
        print(returned_js)
        sa, la, prob_ans, prob_yn = post_process(returned_js, cleaned_html)
        # return_str = page.title + '\t' + page.url + '\n' + ans
        return_str = f'Most related entry: \t{title} \n URL: \t{url}\n\n ' \
                     f'Answerbility score [no-ans vs short vs long]: {prob_ans}\n\n' \
                     f'Long answer: {la}\n\n' \
                     f'Short answer: {sa}\n\n' \
                     f'Yes/no answer [None vs Yes vs No]: {prob_yn}'
        return return_str
        # return json.dumps(res, ensure_ascii=False)

if __name__ == '__main__':
    # qa = QAsystem()
    html = wiki.page('List of rivers by length').html()
    clean = clean_html(html)
    print(find_long_ans((88, 92), clean))
    # page = get_wiki_page('mariachi')
    # html = page.html()
    # print(qa.ask())
    # print(qa.ask('Who wrote the music to Star Wars?'))



#  88 92