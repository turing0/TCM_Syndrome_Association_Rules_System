from __future__ import print_function
from django.shortcuts import render,redirect
from TCMSystem import models
from .myforms import UserForm,RegisterForm,UploadFileForm
from .apriori import *

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans

safe_path = r'D:\\data\\'           # 保存路径
safe_discre_name = 'data_processed.xls'   # 离散处理后的文件的保存名字
# Create your views here.


def index(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        print(form)
        if form.is_valid():
            # file = time.strftime('%Y%m%d%H%M', time.localtime(time.time())) + '_' + str(request.FILES.get('file'))
            file = request.FILES.get('file')
            print('---------------')
            if str(file).find('.xls') == -1:
                message = '请上传excel文件！'
                return render(request, 'index.html',locals())
            datalist = handle_uploaded_file(request.FILES['file'],filename=request.FILES.get('file'))
            message = 'Done! 已将离散处理后的文件保存至 ' + safe_path + safe_discre_name
            valueList = datalist[1::2]
            tlist = apriorirules(safe_path)
            reslist = tlist[0]
            xlist = tlist[1]

            return render(request, 'index.html',locals())
    else:
        form = UploadFileForm()

    return render(request, 'index.html',locals())


def handle_uploaded_file(f,filename):
    filename_path = f'{safe_path}{filename}'  # 生成文件名及路径
    filename = f'{filename}'
    print('path',filename_path)
    with open(filename_path,'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()

    datalist = discre(safe_path, filename)

    return datalist


def discre(path, filename):
    processedfile = path + safe_discre_name  # 数据处理后文件
    apriorifile = path + 'apriori.txt'  # 数据处理后文件
    print(processedfile)
    print(apriorifile)
    typelabel = {u'肝气郁结证型系数': 'A', u'热毒蕴结证型系数': 'B',
                 u'冲任失调证型系数': 'C', u'气血两虚证型系数': 'D',
                 u'脾胃虚弱证型系数': 'E', u'肝肾阴虚证型系数': 'F'}
    k = 4  # 需要进行的聚类类别数
    data = pd.read_excel(path+filename)
    keys = list(typelabel.keys())
    result = pd.DataFrame()
    ap = pd.DataFrame()
    pd.options.mode.chained_assignment = None

    for i in range(len(keys)):
        # 调用k-means算法，进行聚类离散化
        print(u'正在进行“%s”的聚类...' % keys[i])
        kmodel = KMeans(n_clusters=k)  # n_jobs是并行数，一般等于CPU数较好
        kmodel.fit(data[[keys[i]]].values)  # 训练模型

        r1 = pd.DataFrame(kmodel.cluster_centers_, columns=[typelabel[keys[i]]])  # 聚类中心
        r2 = pd.Series(kmodel.labels_).value_counts()  # 分类统计
        r2 = pd.DataFrame(r2, columns=[typelabel[keys[i]] + 'n'])  # 转为DataFrame，记录各个类别的数目
        r = pd.concat([r1, r2], axis=1).sort_values(typelabel[keys[i]])  # 匹配聚类中心和类别数目
        r.index = [1, 2, 3, 4]

        r[typelabel[keys[i]]] = r[typelabel[keys[i]]].rolling(2).mean()  # rolling_mean()用来计算相邻2列的均值，以此作为边界点。
        r[typelabel[keys[i]]][1] = 0.0  # 这两句代码将原来的聚类中心改为边界点。
        result = result.append(r.T)

    lis = {
        'A': '肝气郁结证型系数',
        'B': '热毒蕴结证型系数',
        'C': '冲任失调证型系数',
        'D': '气血两虚证型系数',
        'E': '脾胃虚弱证型系数',
        'F': '肝肾阴虚证型系数',
    }

    for col in 'ABCDEF':
        bins = np.append(result.loc[col, :].values, 1000)
        ap[col + '_cls'] = pd.cut(data[lis[col]], bins=bins, labels=[col + str(i) for i in range(k)],
                                  include_lowest=True)
    ap['H_cls'] = data['TNM分期']

    # print(ap)
    ap.to_csv(apriorifile, index=False,header=False)
    result = result.sort_index()  # 以Index排序，即以A,B,C,D,E,F顺序排
    print(result)
    # print(result.values.tolist())
    result.to_excel(processedfile)

    return result.values.tolist()


def login(request):
    if request.session.get('is_login', None):
        return redirect('/index')

    if request.method == "POST":
        login_form = UserForm(request.POST)
        message = "请检查填写的内容！"
        if login_form.is_valid():
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            try:
                user = models.User.objects.get(username=username)
                if user.password == password:
                    request.session['is_login'] = True
                    request.session['user_id'] = user.id
                    request.session['user_name'] = user.username
                    return redirect('/index/')
                else:
                    message = "密码不正确！"
            except:
                message = "用户不存在！"
        return render(request, 'login.html', locals())
    login_form = UserForm()
    return render(request, 'login.html', locals())


def register(request):
    if request.session.get('is_login', None): # 登录状态不允许注册
        return redirect("/index/")
    if request.method == "POST":
        register_form = RegisterForm(request.POST)
        message = "请检查填写的内容！"
        if register_form.is_valid():
            username = register_form.cleaned_data['username']
            password1 = register_form.cleaned_data['password1']
            password2 = register_form.cleaned_data['password2']
            email = register_form.cleaned_data['email']

            if password1 != password2:
                message = "两次输入的密码不同！"
                return render(request, 'register.html', locals())
            else:

                same_name_user = models.User.objects.filter(username=username)
                if same_name_user:
                    print(same_name_user)
                if same_name_user:  # 用户名唯一
                    print(2)
                    message = '用户已经存在，请重新选择用户名！'
                    return render(request, 'register.html', locals())
                same_email_user = models.User.objects.filter(email=email)
                print(3)
                if same_email_user:  # 邮箱地址唯一
                    message = '该邮箱地址已被注册，请使用别的邮箱！'
                    return render(request, 'register.html', locals())

                # 当一切都OK的情况下，创建新用户
                new_user = models.User.objects.create()
                new_user.username = username
                new_user.password = password1
                new_user.email = email
                new_user.save()
                return redirect('/login/')  # 自动跳转到登录页面

    register_form = RegisterForm()
    return render(request, 'register.html', locals())


def logout(request):
    if not request.session.get('is_login', None):
        return redirect("/index/")
    request.session.flush()
    return redirect("/index/")


def apriorirules(path):
    inputfile = path + 'apriori.txt'  # 输入事务集文件
    data = pd.read_csv(inputfile, header=None, dtype=object)

    # start = time.clock() #计时开始
    print(u'\n转换原始数据至0-1矩阵...')
    ct = lambda x: pd.Series(1, index=x[pd.notnull(x)])  # 转换0-1矩阵的过渡函数
    # b = map(ct, data.as_matrix()) #用map方式执行
    b = map(ct, data.values)
    data = pd.DataFrame(b).fillna(0)  # 实现矩阵转换，空值用0填充
    # end = time.clock() #计时结束
    # print(u'\n转换完毕，用时：%0.2f秒' %(end-start))
    print('\n转换完毕')
    del b  # 删除中间变量b，节省内存

    support = 0.06  # 最小支持度
    confidence = 0.75  # 最小置信度
    ms = '---'  # 连接符，默认'--'，用来区分不同元素，如A--B。需要保证原始表格中不含有该字符

    # start = time.clock() #计时开始
    print(u'\n开始搜索关联规则...')
    result = find_rule(data, support, confidence, ms)
    print(result)
    xlist = result._stat_axis.values.tolist()
    # end = time.clock() #计时结束
    # print(u'\n搜索完成，用时：%0.2f秒' %(end-start))
    print('\n搜索完成')

    return result.values.tolist(), xlist
