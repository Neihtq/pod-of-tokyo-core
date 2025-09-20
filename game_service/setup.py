
from setuptools import setup, find_packages

setup(
    name='game_service',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'Flask',
        'flask-socketio',
        'requests',
        'kubernetes',
        'psycopg2-binary',
        'setuptools',
        'python-dotenv',
        'textual',
        'pytest',
    ],
)
