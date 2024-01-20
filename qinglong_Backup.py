#!/usr/bin/env python3
# coding: utf-8
'''
原项目名称: Ukenn2112 / qinglong_Backup
Author: Ukenn2112
修改：Powerser
功能：自动备份qinglong基本文件至阿里云盘并删除旧文件
Date: 2024年1月20日 上午12:00
cron: 0 2 * * *
new Env('qinglong备份');
'''
import logging
import os
import sys
import tarfile
import time

from aligo import Aligo
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)
try:
    from notify import send
except:
    logger.info("无推送文件")


def env(key):
    return os.environ.get(key)


QLBK_EXCLUDE_NAMES = ['log', '.git', '.github',
                      'node_modules', 'backups', '.pnpm-store']  # 排除目录名
if env("QLBK_EXCLUDE_NAMES"):
    QLBK_EXCLUDE_NAMES = env("QLBK_EXCLUDE_NAMES")
    logger.info(f'检测到设置变量 {QLBK_EXCLUDE_NAMES}')

QLBK_BACKUPS_PATH = 'backups'  # 本地备份目标目录
if env("QLBK_BACKUPS_PATH"):
    QLBK_BACKUPS_PATH = str(env("QLBK_BACKUPS_PATH"))
    logger.info(f'检测到设置变量 {QLBK_BACKUPS_PATH}')

QLBK_CLOUD_PATH = 'backups'  # 默认云端备份目录
if env("QLBK_CLOUD_PATH"):
    QLBK_CLOUD_PATH = str(env("QLBK_CLOUD_PATH"))
    logger.info(f'检测到设置变量 {QLBK_CLOUD_PATH}')

QLBK_MAX_FLIES = 5  # 最大备份保留数量默认5个
if env("QLBK_MAX_FLIES"):
    QLBK_MAX_FLIES = int(env("QLBK_MAX_FLIES"))
    logger.info(f'检测到设置变量 {QLBK_MAX_FLIES}')


def start():
    """开始备份"""
    logger.info('将所需备份目录文件进行压缩...')
    retval = os.getcwd()
    mkdir(QLBK_BACKUPS_PATH)
    now_time = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    files_name = f'{QLBK_BACKUPS_PATH}/qinglong_{now_time}.tar.gz'
    logger.info(f'创建备份文件: {retval}/{files_name}')
    if make_targz(files_name, retval):
        logger.info('备份文件压缩完成...开始上传至阿里云盘')
        remote_folder = ali.get_folder_by_path(f'{QLBK_CLOUD_PATH}')  # 云盘目录
        ali.sync_folder(f'{retval}/{QLBK_CLOUD_PATH}/',  # 上传至网盘
                        flag=True,
                        remote_folder=remote_folder.file_id)
        message_up_time = time.strftime(
            "%Y年%m月%d日 %H时%M分%S秒", time.localtime())
        text = f'已备份至阿里网盘:\n{QLBK_CLOUD_PATH}/qinglong_{now_time}.tar.gz\n' \
               f'\n备份完成时间:\n{message_up_time}\n' \
            #    f'\n项目: https://github.com/Ukenn2112/qinglong_Backup'
        try:
            send('【qinglong自动备份】', text)
        except:
            logger.info("通知发送失败")
        logger.info('---------------------备份完成---------------------')
    else:
        try:
            send('【qinglong自动备份】', '备份压缩失败,请检查日志')
        except:
            logger.info("通知发送失败")
        sys.exit(1)


def make_targz(output_filename, retval):
    """
    压缩为 tar.gz
    :param output_filename: 压缩文件名
    :param retval: 备份目录
    :return: bool
    """
    try:
        tar = tarfile.open(output_filename, "w:gz")
        os.chdir(retval)
        path = os.listdir(os.getcwd())
        for p in path:
            if os.path.isdir(p):
                if p not in QLBK_EXCLUDE_NAMES:
                    pathfile = os.path.join(retval, p)
                    tar.add(pathfile)
        tar.close()
        return True
    except Exception as e:
        logger.info(f'压缩失败: {str(e)}')
        return False


def mkdir(path):
    """创建备份目录"""
    folder = os.path.exists(path)
    if not folder:  # 判断是否存在文件夹如果不存在则创建为文件夹
        logger.info(f'第一次备份,创建备份目录: {QLBK_BACKUPS_PATH}')
        os.makedirs(path)  # 创建文件时如果路径不存在会创建这个路径
    else:  # 如有备份文件夹则检查备份文件数量
        backup_files = f'{run_path}{path}'
        files_all = os.listdir(backup_files)  # backup_files中的所有文件
        logger.info(f'当前备份文件 {len(files_all)}/{QLBK_MAX_FLIES}')
        files_num = len(files_all)
        if files_num > QLBK_MAX_FLIES:
            logger.info(f'达到最大备份数量 {QLBK_MAX_FLIES} 个')
            check_files(files_all, files_num, backup_files, QLBK_MAX_FLIES)


def show(qr_link: str):
    """打印二维码链接"""
    logger.info('请手动复制以下链接，打开阿里网盘App扫描登录')
    logger.info(f'https://cli.im/api/qrcode/code?text={qr_link}')


def fileremove(local_filename):
    """删除旧的备份文件"""
    # 本地文件的完整路径
    local_file_path = os.path.join(QLBK_BACKUPS_PATH, local_filename)

    # 提取文件名，用于构造云端的路径
    cloud_filename = os.path.basename(local_file_path)

    # 云端文件的完整路径
    cloud_file_path = os.path.join(QLBK_CLOUD_PATH, cloud_filename)

    # 删除本地文件
    if os.path.exists(local_file_path):
        os.remove(local_file_path)
        logger.info('已删除本地旧的备份文件: %s' % local_file_path)
    else:
        logger.info('本地旧的备份文件不存在: %s' % local_file_path)

    # 删除云端文件
    remote_file = ali.get_file_by_path(cloud_file_path)
    if remote_file is not None:
        ali.move_file_to_trash(file_id=remote_file.file_id)
        logger.info('已删除云盘旧的备份文件: %s' % cloud_file_path)
    else:
        logger.info('未找到云端旧的备份文件: %s' % cloud_file_path)



def check_files(files_all, files_num, backup_files, QLBK_MAX_FLIES):
    """检查并删除最旧的备份文件"""
    create_time = []
    file_name = []
    for names in files_all:
        if names.endswith(".tar.gz"):
            filename = os.path.join(backup_files, names)
            file_name.append(filename)
            create_time.append(os.path.getctime(filename))  # 获取文件的创建时间

    # 将文件按创建时间排序
    dit = dict(zip(create_time, file_name))
    sorted_files = sorted(dit.items(), key=lambda d: d[0])  # 按时间升序排序

    # 删除最旧的文件直到达到设定的最大文件数
    for i in range(files_num - QLBK_MAX_FLIES):
        oldest_file = sorted_files[i][1]
        fileremove(os.path.basename(oldest_file))



if __name__ == '__main__':
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logger.info('---------' + str(nowtime) + ' 备份程序开始执行------------')
    if os.path.exists('/ql/data/'):
        logger.info('检测到data目录，切换运行目录至 /ql/data/')
        run_path = '/ql/data/'
    else:
        run_path = '/ql/'
    os.chdir(run_path)  # 设置运行目录
    logger.info('登录阿里云盘')
    try:
        ali = Aligo(level=logging.INFO, show=show)
    except:
        logger.info('登录失败')
        try:
            send('【qinglong自动备份】', '阿里网盘登录失败,请手动重新运行本脚本登录')
        except:
            logger.info("通知发送失败")
        sys.exit(1)
    start()
    sys.exit(0)
