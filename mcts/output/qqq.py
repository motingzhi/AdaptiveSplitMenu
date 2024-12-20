
import numpy as np
import matplotlib.pyplot as plt
#产生测试数据
x = [1,2,3,4,5]
y = [0.97,0.88,0.93,0.91,0.81]
fig = plt.figure()
ax1 = fig.add_subplot(111)
#设置标题
ax1.set_title('Scatter Plot')
#设置X轴标签
plt.xlabel('X')
#设置Y轴标签
plt.ylabel('Y')
#画散点图
ax1.scatter(x,y,c = 'r',marker = 'o')
#设置图标
plt.legend('x1')
#显示所画的图
plt.show()
