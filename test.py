
# def transform(self, a,b,c,d,e,f):
#         """adjoin a mathematical transform to the current graphics state matrix.
#            Not recommended for beginners."""
#         #How can Python track this?
#         if ENABLE_TRACKING:
#             a0,b0,c0,d0,e0,f0 = self._currentMatrix
#             self._currentMatrix = (a0*a+c0*b,    b0*a+d0*b,
#                                    a0*c+c0*d,    b0*c+d0*d,
#                                    a0*e+c0*f+e0, b0*e+d0*f+f0)

# a = 0.12467625
# b = 0.0511335
# c= -0.05446875
# d = 0.13280775
# e = 166.6683067
# f = 676.6863895

# 0.894427191	0.447213595
5.520015225
5.640007542

# a = 0.894427191
# b = 0.447213595
# c = -0.447213595
# d = 0.894427191
# e = 161.177554
# f = 435.4869999
166.9806523
169.8563515
x = 166.9806523
y = 169.8563515
c = 0
d = 0
e = 0
f = 0

# a0 = 0.134766
# b0 = 0
# c0 = 0
# d0 = 0.1376955
# e0 = 161.177554
# f0 = 435.4869999

a0 = 0.894427191
b0 = -0.447213595
c0 = 0.447213595
d0 = 0.894427191
e0 = 166.9806523-6
f0 = 169.8563515-6

# currentMatrix = (a0*a+c0*b,    b0*a+d0*b,
#                 a0*c+c0*d,    b0*c+d0*d,
#                 a0*e+c0*f+e0, b0*e+d0*f+f0)

p1 = (x*a0-y*b0+e0-e0*a0+f0*b0,x*a0+y*b0+e0-e0*a0-f0*b0)

# print(currentMatrix)
print(p1)
