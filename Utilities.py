from threading import Thread # 多線程平行化處理用
PARELLEL_DEGREE = 4

#
def parallelly_process(func, divide_param, other_args=[], kwargs={}):
    partLst_s = divide_into_n_parts(divide_param, PARELLEL_DEGREE)

    threads = []
    # 為n個部分各設一個thread來
    for partLst in partLst_s:
        total_args = [partLst] + other_args
        thread = ThreadWithReturnValue(target=func, args=total_args, kwargs=kwargs)
        threads.append(thread)

    # 讓所有thread開始跑
    for thread in threads:
        thread.start()

    # 所有thread都執行完畢後才讓你往下
    returnValues = []
    for thread in threads:
        returnValues.append(thread.join())

    return returnValues


def divide_into_n_parts(lst, n):
    return [lst[i::n] for i in range(n)]

    # [startIndex : endIndex : skip]
    # Example:
    # Divide [0, 1, 2, 3, 4, 5, 6, 7, 8 ,9, 10, 11, 12] into 3 parts
    # -> [[0, 3, 6, 9, 12], [1, 4, 7, 10], [2, 5, 8, 11]]

class ThreadWithReturnValue(Thread):
    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self):
        Thread.join(self)
        return self._return
