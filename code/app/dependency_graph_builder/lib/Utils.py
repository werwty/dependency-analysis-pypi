import os
import time
import sys

import requests


def download_file(url, **kwargs):
    def info(text, ln=True):
        sys.stdout.write(text)
        if ln:
            print("")

    warn = info
    error = info
    succ = info

    def gen_size_str(value):
        value = int(value)
        if value <= 1024:
            return u'%s B' % value
        if value <= 1024 * 1024:
            return u'%s KB' % (value // 1024)
        if value <= 1024 * 1024 * 1024:
            return u'%s MB' % (value // (1024 * 1024))
        else:
            return u'%s GB' % (value // (1024 * 1024 * 1024))

    def update_status_bar(r_speed, size, received):
        r_speed = int(r_speed)
        size = int(size)
        received = int(received)

        done = int(50 * (float(received) / float(size)))
        info(u"\r[%s%s] %s/s        " % (u'=' * done, u' ' * (50 - done), gen_size_str(r_speed)), False)

    local_filename = kwargs.get("filename", None)
    base_path = kwargs.get("path", None)
    retry_max = kwargs.get("retry_max", -1)
    retry_delay = kwargs.get("retry_delay", 1)
    retry_cnt = 1

    if not local_filename:
        local_filename = url.split(u'/')[-1]

    if base_path:
        local_filename = os.path.abspath(base_path) + u'/' + local_filename

    info(u"Downloading to %s" % local_filename)

    while True:
        r = requests.get(url, stream=True)

        if r.status_code == 202:
            if retry_max >= 0:
                if retry_cnt <= retry_max:
                    warn(u'Get HTTP 202 response, retry after %d seconds (%s/%s)...' % (
                    retry_delay, retry_cnt, retry_max))
                    retry_cnt = retry_cnt + 1
                else:
                    error(u'Get HTTP 202 response, stop retry (%s), download fail' % retry_max)
                    return False
            else:
                pass
                warn(u'Get HTTP 202 response, retry after %s seconds...' % retry_delay)
            time.sleep(retry_delay)
        elif r.status_code != 200:
            error(u'HTTP %s, download fail' % r.status_code)
            return False
        else:
            break

    file_start_time = time.perf_counter()
    total_length = int(r.headers.get(u'content-length'))
    received_length = 0

    with open(local_filename, 'wb') as f:
        chunk_start_time = time.perf_counter()
        for chunk in r.iter_content(chunk_size=(1024 * 64)):
            time_elapse = time.perf_counter() - chunk_start_time
            chunk_start_time = time.perf_counter()

            received_length = received_length + len(chunk)
            speed = len(chunk) / time_elapse
            update_status_bar(speed, total_length, received_length)

            if chunk:
                f.write(chunk)

    info(u'\r[%s]' % (u'=' * 50), False)
    succ(u'\t\t\t [DONE]')

    download_time = time.perf_counter() - file_start_time
    info(u'Download complete, takes %.1f seconds, size %s, avg. speed %s/s        ' % (
        download_time, gen_size_str(total_length), gen_size_str(total_length / download_time)))
    return local_filename
