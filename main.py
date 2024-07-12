# -*- coding: utf-8 -*-
# @Time    : 2024/6/30 17:52
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : main.py


from utils import timeit_decorator


@timeit_decorator
def main():
    print("Program completed successfully.")


if __name__ == "__main__":
    main()
