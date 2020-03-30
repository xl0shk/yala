# -*- coding: utf-8 -*-
from yalamain import create_app

app = create_app('development')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=30010, debug=True)
