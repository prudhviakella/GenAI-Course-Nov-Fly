def process_file(file_path):
    with open(file_path,'r') as f:
       for line in f:
           yield line

#file_gen = process_file('/Users/akellaprudhvi/mystuff/Course/GenAI-Course-Modules/Module_3/employee.csv')

# print(next(file_gen))
# print(next(file_gen))
# print(next(file_gen))
# print(next(file_gen))
# print(next(file_gen))
# print(next(file_gen))


# for line in process_file('/Users/akellaprudhvi/mystuff/Course/GenAI-Course-Modules/Module_3/employee.csv'):
#     print(line)

list_comp = [line for line in open('/Users/akellaprudhvi/mystuff/Course/GenAI-Course-Modules/Module_3/employee.csv','r')]
print(list_comp)
gen = (line for line in open('/Users/akellaprudhvi/mystuff/Course/GenAI-Course-Modules/Module_3/employee.csv','r'))
tupe = (1,2,3,4,5)
for line in gen:
    print(line)
print(type(gen))
print(type(tupe))