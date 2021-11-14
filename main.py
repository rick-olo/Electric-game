# 本代码所有可视化部分，建议仅调试模块时候选择性使用，因为过多的图像绘制会对线条检测、色块检测、数字识别产生较大影响。
# 实测部署时建议关闭所有可视化部分。

# 2021-11-07 v1.0
# Designed By 燕郊码怪
# 2021-11-08 v1.1
# Designed By 陈四海
# 2021-11-12 v1.2
# Designed By 陈四海
# 命名规则
# 变量名--下划线命名法/函数名--小驼峰命名法

#--------------------【import】------------------------
import sensor, image, time, math # 基础库
from pyb import UART,LED # 串口通信
from image import SEARCH_EX, SEARCH_DS # 模板匹配

#--------------------【初始化】------------------------
sensor.reset()
sensor.set_framesize(sensor.QQVGA) # 适用于 OpenMV4 H7 处理能力的图像分辨率
sensor.set_pixformat(sensor.RGB565) # 获取彩色图 RGB565, 灰度图 GRAYSCALE
sensor.skip_frames(time = 2000) # 让初始化生效
clock = time.clock()

uart = UART(3,115200)   #定义串口3变量
uart.init(115200, bits=8, parity=None, stop=1) # 初始化串口信息


#--------------------【全局变量】------------------------

#dectection_flag = True # 是否获取到病房号【True为没有(初始状态)，False为已接收】
target_num = None # 目标病房号数字初始化

#red_threshold = (18, 69, 18, 127, -5, 55) # 检测红色线条的LAB像素阈值(建议根据实际环境情况调整)

#last_value = 80 # 默认道路分离线初始化值为画面中心
#pos_result = 0 # 默认没有检测到地面数字标签
#driver_process = [] # 用于存储小车转向信息(用于倒车)

##状态位
process = 0 #0--获取病房号|1--送药|2--倒车

##串口发送信息
#number 识别到的数字【十六进制】
number = 0xf0
#0x01 ---- 识别到数字1
#0x02 ---- 识别到数字2
#0xf0 ---- 未识别到数字
#0xff ---- 开始送药任务

#sigal 偏转角【int】
angle = 0
#0 ---- 未开始寻找病房

#state 状态【十六进制】
state = 0xf0
#0x01 ---- 正常/直行
#0x02 ---- 左前
#0x03 ---- 右前
#0x04 ---- 校准*
#0x05 ---- 到达

#0xf0 ---- 未识别到目标病房号
#0xff ---- 确认识别到目标病房号

#--------------------【绘图模式】------------------------
#          【True -- 开启 |False -- 关闭】
darw_number_rect = False        #数字识别确认框
draw_get_number = False          #获取病房号Roi框

#--------------------【函数定义】------------------------

# 模板匹配数字(1~8号)【return：states 十六进制 当前状态信息】
def templateMatch(img, imgPath): # 【图像、模板路径】
    numRoi = [2,10,155,60] # 数字识别区域【记得和drowWindows函数内numRoi同步更改】
    img_bat = img.copy()
    img_bat.to_grayscale() # 彩色图转换为灰度图

    if process == 0: #获取病房号状态
        # model_template #,roi=[5,10,150,50]
        template = image.Image("/target_template/"+str(imgPath)+".pgm") # 药房任务接受模板匹配
        r = img_bat.find_template(template, 0.80, roi=[30,10,100,100], step=1, search=SEARCH_EX)
        if r:
            states = 0xff         #已识别到目标病房号
        else:
            states = 0xf0         #未识别到目标病房号
    else:#识别病房号状态
        # 尝试匹配左模板
        template = image.Image("/model_template/"+str(imgPath)+"_l.pgm") # 病房任务模板匹配（左侧）
        r = img_bat.find_template(template, 0.80, roi=numRoi, step=1, search=SEARCH_EX) # roi=[5,10,150,50]
        if r : # 在左侧是否识别到
            states = 0x02         #左转
        else:  #在右侧是否识别到
            template = image.Image("/model_template/"+str(imgPath)+"_r.pgm") # 病房任务模板匹配（右侧）
            r = img_bat.find_template(template, 0.80, roi=numRoi, step=1, search=SEARCH_EX)
            if r:
                states = 0x03     #右转
            else:
                states = 0x01     #未识别到数字 状态正常
     ##【绘图部分】
    if darw_number_rect :#识别到数字时绘出包裹矩形
        img.draw_rectangle(numRoi)
        if r:
            img.draw_rectangle(r, color=(255,0,255)) # 图像中画出匹配框
    if draw_get_number and state == 0xf0:#获取病房号roi
        img.draw_rectangle([30,10,100,100])
    ## 函数返回
    return states


    #img.binary([red_threshold]) # 二值化图像，分离线条
    #img1.lens_corr(1.1) # 相机畸变矫正

    ## 像素点阈值，直线搜索时的进步尺寸的单位半径，直线搜索时的进步尺寸的单位角度
    #for l in img.find_lines(threshold = 12000, theta_margin = 55, rho_margin = 55): # 20000  55 55
        #print(l.x1(),l.y1(),l.theta(),l.magnitude(),l.rho())
        #if abs(l.theta()-90) < 30: # 横线检测(红色) （60~120）
            #print("检测横线角度为：",l.theta())
            #img.draw_line(l.line(), color = (255, 0, 0))
        #if l.theta() > 160 or l.theta() < 20: # 竖线检测(绿色) （160~180，0~20）
            #print("检测竖线角度为：",l.theta())
            #img.draw_line(l.line(), color = (0, 255, 0))
        ##img.draw_line(l.line(), color = (0, 255, 0))
    #img.draw_rectangle([5,10,150,50]) # 画预判框
    #img.draw_rectangle([55,10,50,50]) # 画预判框(160)
    #return 0

# 小车巡线【return: Float 小车偏离直线角度】
def lineFlowing(img):
    RED_THRESHOLD = [(18, 69, 18, 127, -5, 55)]
    # 每个roi为(x, y, w, h)，线检测算法将尝试找到每个roi中最大的blob的质心。
    # 然后用不同的权重对质心的x位置求平均值，其中最大的权重分配给靠近图像底部的roi，
    # 较小的权重分配给下一个roi，以此类推。

    #roi代表三个取样区域，（x,y,w,h,weight）,代表左上顶点（x,y）宽高分别为w和h的矩形，
    #weight为当前矩形的权值。注意本例程采用的QQVGA图像大小为160x120，roi即把图像横分成三个矩形。
    #三个矩形的阈值要根据实际情况进行调整，离机器人视野最近的矩形权值要最大，
    #如上图的最下方的矩形，即(0, 100, 160, 20, 0.7)
    ROIS = [ # [ROI, weight](在值的设置有意避免了边角处畸变引起的计算问题)
            (30, 90, 85, 20, 0.7), # 下侧检测区
            (0, 50, 160, 20, 0.3), # 中侧检测区
            (40, 005, 80, 10, 0.1) # 上侧检测区
           ]
    weight_sum = 0 #权值和初始化
    for r in ROIS: weight_sum += r[4]
    #计算权值和。遍历上面的三个矩形，r[4]即每个矩形的权值。
    most_pixels = 80 # 默认最小色块像素总量
    centroid_sum = 0
    #利用颜色识别分别寻找三个矩形区域内的线段
    for r in ROIS:
        blobs = img.find_blobs(RED_THRESHOLD, roi=r[0:4], merge=True)
        # r[0:4] is roi tuple.
        #找到视野中的线,merge=true,将找到的图像区域合并成一个
        #目标区域找到直线
        if blobs:
            # 查找像素最多的blob的索引。
            largest_blob = 0
            for i in range(len(blobs)):
            #目标区域找到的颜色块（线段块）可能不止一个，找到最大的一个，作为本区域内的目标直线
                if blobs[i].pixels() > most_pixels:
                    if blobs[i].rect()[2]/blobs[i].rect()[3] > 1: # 过滤横向的色块(通常它们是路口或横行的直线)
                        continue
                    most_pixels = blobs[i].pixels()
                    #merged_blobs[i][4]是这个颜色块的像素总数，如果此颜色块像素总数大于
                    #most_pixels，则把本区域作为像素总数最大的颜色块。更新most_pixels和largest_blob
                    largest_blob = i
            # 在色块周围画一个矩形。
            img.draw_rectangle(blobs[largest_blob].rect(),color=(255,255,0))
            # 将此区域的像素数最大的颜色块画矩形和十字形标记出来
            img.draw_cross(blobs[largest_blob].cx(),
                           blobs[largest_blob].cy(),
                           color=(255,255,0))
            centroid_sum += blobs[largest_blob].cx() * r[4] # r[4] is the roi weight.
            #计算centroid_sum，centroid_sum等于每个区域的最大颜色块的中心点的x坐标值乘本区域的权值
    center_pos = (centroid_sum / weight_sum) # Determine center of line.
    #中间公式
    # 将center_pos转换为一个偏角。我们用的是非线性运算，所以越偏离直线，响应越强。
    # 非线性操作很适合用于这样的算法的输出，以引起响应“触发器”。
    deflection_angle = 0 # 初始化机器人应该转的角度
    # 80是X的一半，60是Y的一半。
    # 下面的等式只是计算三角形的角度，其中三角形的另一边是中心位置与中心的偏差，相邻边是Y的一半。
    # 这样会将角度输出限制在-45至45度左右。（不完全是-45至45度）。
    deflection_angle = -math.atan((center_pos-80)/60)    #角度计算.80 60 分别为图像宽和高的一半，图像大小为QQVGA 160x120.    #角度计算.80 60 分别为图像宽和高的一半，图像大小为QQVGA 160x120. #注意计算得到的是弧度值
    deflection_angle = math.degrees(deflection_angle) #将计算结果的弧度值转化为角度值
    # 现在你有一个角度来告诉你该如何转动机器人。通过该角度可以合并最靠近机器人的部分直线和远离机器人的部分直线，以实现更好的预测。
    #print("解算偏离角度: %f" % deflection_angle)
    return deflection_angle

# 检测路口情况【return: Int 路口情况分类】
def crossRoadDetection(img):
    RED_THRESHOLD = [(18, 69, 18, 127, -5, 55)] #如果是黑线[(0, 64)] #如果是白线[(128，255)]
    ROIS = [
            (65, 3, 30, 30), # 上侧检测区
            (18, 92, 44, 24), # 左侧检测区
            (98, 92, 47, 24), # 右侧检测区
            (65, 49, 30, 70) # 下侧检测区
           ]
    most_pixels = 80 # 目标区块最小面积
    #利用颜色识别分别寻找三个矩形区域内的线段
    roi_region = [] # 区域(用于存储转向逻辑判断)
    counter_roi = 0 # 默认从第一个区域开始计数(用于判断哪个区域存在道路线)
    for r in ROIS:
        redLineFlag = 0 # 红线存在标志位初始化
        counter_roi += 1
        blobs = img.find_blobs(RED_THRESHOLD, roi=r[0:4], merge=True) #找到视野中的线,merge=true,将找到的图像区域合并成一个
        #目标区域找到直线
        if blobs:
            # 查找像素最多的blob的索引。
            largest_blob = 0
            for i in range(len(blobs)):
            #目标区域找到的颜色块（线段块）可能不止一个，找到最大的一个，作为本区域内的目标直线
                if blobs[i].pixels() > most_pixels:
                    most_pixels = blobs[i].pixels()
                    #merged_blobs[i][4]是这个颜色块的像素总数，如果此颜色块像素总数大于
                    #most_pixels，则把本区域作为像素总数最大的颜色块。更新most_pixels和largest_blob
                    largest_blob = i
            # 在色块周围画一个矩形。
            img.draw_rectangle(blobs[largest_blob].rect())
            # 将此区域的像素数最大的颜色块画矩形和十字形标记出来
            img.draw_cross(blobs[largest_blob].cx(),
                           blobs[largest_blob].cy())
            redLineFlag = 1 # 检测到红线更新标志位
        if redLineFlag == 1: # 检测后对应位置为1
           roi_region.insert(counter_roi-1, 1)
        else: roi_region.insert(counter_roi-1, 0) # 未检测对应位置为0
    traffic_result = trafficLogic(roi_region) # 道路口逻辑判断
    return traffic_result

# 道路情况逻辑判断【return: Int 路口情况分类】
def trafficLogic(roi_region):
    traffic_result = 0 # 初始化
    if roi_region == [1,0,0,1]:
        #print("当前直线向前")
        traffic_result = 1
    elif roi_region == [1,1,1,1]:
        #print("当前为十字路口")
        traffic_result = 2
    elif roi_region == [0,1,1,1]:
        #print("当前正对T字路口")
        traffic_result = 3
    elif roi_region == [1,1,0,1]:
        #print("当前T字路口向左")
        traffic_result = 4
    elif roi_region == [1,0,1,1]:
        #print("当前T字路口向右")
        traffic_result = 5
    elif roi_region == [0,0,0,1]:
        #print("已经到达道路尽头")
        traffic_result = 6
    elif roi_region == [0,0,0,0]:
        #print("当前已经跑偏或未检测到赛道")
        traffic_result = 7
    return traffic_result # 返回逻辑判断结果

# 偏转角串口 【return: 无】
def signal(angle,state):
    ##-------------|------|---------------|-----|------|
    ##             | 帧头  |    偏转角      | 状态 | 帧尾  |
    FH = bytearray([ 0x2C , int(angle+3) ,state, 0x5B ])
    uart.write(FH)



# 【未用】道路分界检测【return: Int 获取道路中间分界线X值】
#def crossRoadSeparate(img, red_threshold, last_value): # 引入了last_value, 保证分界线的连续检出。
    #img_bin = img.copy()
    #img_bin.binary([red_threshold]) # 二值化图像，分离线条
    #img_bin.lens_corr(1.1) # 相机畸变矫正【一般可以不用】
    #min_degree = 20 # 霍夫变换角度最小值
    #max_degree = 160 # 179 # 霍夫变换直线角度最大值
    #pixel_threshold = 10000 # 像素点阈值
    #theta_margins = 25 # 直线搜索时的进步尺寸的单位半径
    #rho_margins = 25 # 直线搜索时的进步尺寸的单位角度
    #for l in img_bin.find_lines(threshold = pixel_threshold, theta_margin = theta_margins, rho_margin = rho_margins):
        ##print(l.x1(),l.y1(),l.theta(),l.magnitude(),l.rho()) # 调参看值用
        #if l.theta() > max_degree or l.theta() < min_degree: # 竖线检测(绿色) （角度范围为 160~180，0~20）
            ##img.draw_line(l.line(), color = (0, 255, 0)) # 显示中间线
            #if l != None: # 若检测到直线，则视为道路分界线【这里有个小Trick,保证调试设置好合理阈值后，视为第一个检测到的直线作为分界线】
                #return l.x1()
    #return last_value # 若本轮未检测到直线，则用最近历史值作为分界线

# 【弃用】绘图函数(用于调试可视化)【实测部署时建议关闭所有可视化部分】
#def drowWindows(img, rois=None, lines=None):
    #numRoi = [2,10,155,60] # 数字识别区域【记得和templateMatch函数内numRoi同步更改】
    #img.draw_rectangle(numRoi)
    ##img.draw_rectangle([30,10,100,100])
    ## 绘制检测道路口形状的四个区域
    #img.draw_rectangle([65, 3, 30, 10],color=(0,255,0)) # 上侧
    #img.draw_rectangle([18, 15, 44, 24],color=(0,255,0)) # 左侧
    #img.draw_rectangle([98, 15, 47, 24],color=(0,255,0)) # 右侧
    #img.draw_rectangle([65, 49, 30, 60],color=(0,255,0)) # 下侧

# 【弃用】处理下位机信息【TODO: 用于处理下位机反馈的消息】
#def backUp(task):
    #if task == 1: # 倒车
        #pass

# 【弃用】事件处理与下位机通信【TODO: 丰富事件库】
#def message(pos, pos_result, traffic_result):
    #if pos == 1: # 去1号病房不需要检测数字
        #if traffic_result == 2: # 十字路口
            #print("向左转进入1号病房")
    #elif pos == 2: # 去2号病房不需要检测数字
        #if traffic_result == 2: # 十字路口
            #print("向左转进入2号病房")
    #if pos_result == 0: # 未能检测到目标
        #if traffic_result == 0: # 错误码：异常情况
            #pass
        #elif traffic_result == 1: # 沿线前进
            #print("沿线前进")
        #elif traffic_result == 2: # 十字路口
            #print("十字路口")
        #elif traffic_result == 3: # 正对T字路口
            #pass
        #elif traffic_result == 4: # T字路口向左
            #print("T字路口向左")
        #elif traffic_result == 5: # T字路口向右
            #print("T字路口向右")
        #elif traffic_result == 6: # 已经到达道路尽头
            #print("已经到达道路镜头")
        #elif traffic_result == 7: # 跑偏或驶离赛道
            #pass
    #elif pos_result == 1: # 检测目标在左侧
        #if traffic_result == 0: # 错误码：异常情况
            #pass
        #elif traffic_result == 1: # 沿线前进
            #pass
        #elif traffic_result == 2: # 十字路口
            #print("十字路口左转弯")
        #elif traffic_result == 3: # 正对T字路口
            #print("T字路口左转弯")
    #elif pos_result == 2: # 检测目标在右侧
        #if traffic_result == 0: # 错误码：异常情况
            #pass
        #elif traffic_result == 1: # 沿线前进
            #pass
        #elif traffic_result == 2: # 十字路口
            #print("十字路口右转弯")
        #elif traffic_result == 3: # 正对T字路口
            #print("T字路口右转弯")
    ##if traffic_result == 7:
        ##VISIONWORK =  # 视觉开始工作
        ##mess = VISIONWORKbytearray([0x2c,0x01,0x5b])
    ##elif traffic_result == 2:
        ##VISIONPAUSE = bytearray([0x2c,0x02,0x5b]) # 视觉停止工作
        ##mess = VISIONPAUSE
    ##elif traffic_result == 3:
        ##TEMPLATE_OK = bytearray([0x2c,0x03,0x5b]) # 完成模板匹配
        ##mess = TEMPLATE_OK
    ##elif traffic_result == 4:
        ##TEMPLATE_FAIL = bytearray([0x2c,0x04,0x5b]) # 模板匹配失败
        ##mess = TEMPLATE_FAIL
    ##elif traffic_result == 5:
        ##CROSSROAD_OK = bytearray([0x2c,0x05,0x5b]) # 完成路口检测
        ##mess = CROSSROAD_OK
    ##elif traffic_result == 6:
        ##CROSSROAD_FAIL = bytearray([0x2c,0x06,0x5b]) # 路口检测失败
        ##mess = CROSSROAD_FAIL
    ##elif traffic_result == 1:
        ##CROSSROAD_STREET = bytearray([0x2c,0x07,0x5b]) # 路口直行
        ##mess = CROSSROAD_STREET
    ##elif traffic_result == 8:
        ##CROSSROAD_LEFT = bytearray([0x2c,0x08,0x5b]) # 路口左转
        ##mess = CROSSROAD_LEFT
    ##elif traffic_result == 9:
        ##CROSSROAD_RIGHT = bytearray([0x2c,0x09,0x5b]) # 路口右转
        ##mess = CROSSROAD_RIGHT
    ##else: # 未能匹配上述事件
        ##Fail = bytearray([0x2c,0x10,0x5b]) # 错误
        ##mess = Fail
    ##uart.write(mess)
    ##return 1 # 允许检测

# 【弃用】小车转向判断【return: Int 返回转向结果(0:未检测到 1:左转 2:右转)】
#def turnLogic(target_num, divideLine):
    #turnResult = 0 # 初始化检测标志
    #if (target_num[0] - divideLine) > 0: # 若大于0，则目标在分界线右侧。反之则目标在分界线左侧
        #turnResult = 2
    #else:
        #turnResult = 1
    #return turnResult

#--------------------【主函数】------------------------
while(True):
    # 初始化
    clock.tick()#时钟
    img = sensor.snapshot()#捕获一帧图像
    img.lens_corr(1.1) # 相机畸变矫正

    #last_value = crossRoadSeparate(img, red_threshold, last_value) # 道路左右侧分界检测(time ~ 0.8FPS)

    # 程序开始
    # 未获取病房号
    if process == 0:# 【0--获取送药任务中】
        for i in [1,2,8,4,6,5,3,7]: # 将易误识别数字顺序进行了调整(主要针对8、6、5、3)
            number =  templateMatch(img, i)#获取病房号
            if number == 0xff:#如果获取到
               target_num = i # 获得目标数字为i
               #if target_num == 1:number = 0x02 #发送数字1
               #elif target_num == 2:number = 0x03 #发送数字2
               process = 1#开始送药任务
               state = 0x01
               print("目标病房号已明确，为:",target_num)
               break
        continue
    #已获取到病房号
    if process == 1:# 【1--识别到病房好,开始寻找红线】
        now = crossRoadDetection(img)
        if now != 7:
            process = 2
    if process == 2:# 【2--识别到红线，开始寻找病房】
        ## 1-寻迹 角度矫正
        angle = lineFlowing(img)#angle--float类型角度数据

        ## 2-数字是识别
        #state = templateMatch(img, target_num)#通过是否识别到数字获取状态

        ## 3-路口情况识别
        is_end = crossRoadDetection(img)
        if is_end == 2 and target_num == 1:
            process = 3
            print("左转")
            state = 0x02
        elif is_end == 2 and target_num == 2:
            process = 3
            state = 0x03
            print("右转")
        continue
    if process == 3:# 【2--倒车】
        #state = 0x01
        is_end = crossRoadDetection(img)
        if is_end == 7:
            state = 0x05
            print("到达")
        angle = lineFlowing(img)#angle--float类型角度数据
    ## 串口通信
    signal(angle,state)

    #print(clock.fps()) # 显示耗时
