def doh2():
		yield "Homer: Hi"
		yield "Marge: A deer"
		yield "Lisa: Mona Lisa"
		
for d in doh2():
	print(d)