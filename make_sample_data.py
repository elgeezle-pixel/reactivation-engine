#name = "Amina"
#phone = "08063802492"
#print(name) 
#print(phone)

#name = "Amina"
#service = "business"

#message = f"Hi {name},please tell us about your {service} needs."
#print(message)

#names = ['Amina', 'Chinedu', 'Tunde']
#service = "business"

#print(names)
#print(names[0])

 #days_since_contact = 200
 #if days_since_contact < 60:
 #   print("Hot lead - call this one")
 #else:
 #   print("cold lead - send a message")
 
#print(f"Hi {person}, please tell us about your {service} needs.")

leads = [ 
{"name": "Amina", "days_since_contact":45},
{"name": "Chinedu", "days_since_contact":200},
{"name": "Tunde", "days_since_contact":90},
]

for lead in leads:
	if lead["days_since_contact"] < 60:
		print(f'{lead["name"]}: Hot - call this one')
	else:
		print(f'{lead["name"]}: Cold - send a message')
