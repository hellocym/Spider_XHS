import json
import re
import requests
from one import OneNote
from xhs_utils.xhs_util import get_headers, get_search_data, get_params, js, check_cookies
from queue import Queue
import threading


class Search:
    def __init__(self, cookies=None, thread_num=10):
        if cookies is None:
            self.cookies = check_cookies()
        else:
            self.cookies = cookies
        self.search_url = "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes"
        self.headers = get_headers()
        self.params = get_params()
        self.oneNote = OneNote(self.cookies)
        self.thread_num = thread_num

    def get_search_note(self, query, number):
        data = get_search_data()
        api = '/api/sns/web/v1/search/notes'
        data = json.dumps(data, separators=(',', ':'))
        data = re.sub(r'"keyword":".*?"', f'"keyword":"{query}"', data)
        page = 0
        note_ids = []
        while len(note_ids) < number:
            page += 1
            data = re.sub(r'"page":".*?"', f'"page":"{page}"', data)
            ret = js.call('get_xs', api, data, self.cookies['a1'])
            self.headers['x-s'], self.headers['x-t'] = ret['X-s'], str(ret['X-t'])
            response = requests.post(self.search_url, headers=self.headers, cookies=self.cookies, data=data.encode('utf-8'))
            res = response.json()
            if not res['data']['has_more']:
                print(f'搜索结果数量为 {len(note_ids)}, 不足 {number}')
                break
            items = res['data']['items']
            for note in items:
                note_id = note['id']
                note_ids.append(note_id)
                if len(note_ids) >= number:
                    break
        return note_ids

    def handle_note_info(self, query, number, sort, path, need_cover=False):
        data = get_search_data()
        data['sort'] = sort
        api = '/api/sns/web/v1/search/notes'
        data = json.dumps(data, separators=(',', ':'))
        data = re.sub(r'"keyword":".*?"', f'"keyword":"{query}"', data)
        page = 0
        index = 0
        while index < number:
            page += 1
            data = re.sub(r'"page":".*?"', f'"page":"{page}"', data)
            ret = js.call('get_xs', api, data, self.cookies['a1'])
            self.headers['x-s'], self.headers['x-t'] = ret['X-s'], str(ret['X-t'])
            response = requests.post(self.search_url, headers=self.headers, cookies=self.cookies, data=data.encode('utf-8'))
            res = response.json()
            try:
                items = res['data']['items']
            except:
                print(f'搜索结果数量为 {index}, 不足 {number}')
                break
            for note in items:
                index += 1
                self.oneNote.save_one_note_info(self.oneNote.detail_url + note['id'], need_cover, '', path)
                if index >= number:
                    break
            if not res['data']['has_more'] and index < number:
                print(f'搜索结果数量为 {index}, 不足 {number}')
                break
        print(f'搜索结果全部下载完成，共 {index} 个笔记')

    def handle_note_info_multithread(self, query, number, sort, path, need_cover=False):
        note_ids = self.get_search_note(query, number)
        queue = Queue()
        for note_id in note_ids:
            queue.put(note_id)

        def worker():
            while not queue.empty():
                note_id = queue.get()
                try:
                    self.oneNote.save_one_note_info(self.oneNote.detail_url + note_id, need_cover, '', path)
                finally:
                    queue.task_done()

        threads = []
        for _ in range(self.thread_num):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)

        queue.join()  # Wait for the queue to become empty.

        for _ in range(len(threads)):
            queue.put(None)  # Signal for threads to exit

        for t in threads:
            t.join()  # Wait for all threads to finish

        print(f'多线程搜索结果全部下载完成，共 {len(note_ids)} 个笔记')




    def main(self, info):
        query = info['query']
        number = info['number']
        sort = info['sort']
        path = info['path']
        self.handle_note_info_multithread(query, number, sort, path, need_cover=True)


if __name__ == '__main__':
    search = Search()
    # 搜索的关键词 
    query = '上海 名人'
    # 搜索的数量（前多少个）
    number = 1000
    # 排序方式 general: 综合排序 popularity_descending: 热门排序 time_descending: 最新排序
    sort = 'general'
    info = {
        'query': query,
        'number': number,
        'sort': sort,
        'path': 'datas_celebrity'
    }
    search.main(info)
