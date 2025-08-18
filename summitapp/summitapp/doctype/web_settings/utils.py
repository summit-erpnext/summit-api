
def add_category_from_sub(self, sc_field, c_field):
	categories = []
	if self.get(sc_field):
		self.set(c_field,[])
		for row in self.get(sc_field):
			if row.category not in categories:
				categories.append(row.category)
	
	existing = [row.name1 for row in (self.get(c_field) or [])]
	if categories:
		for category in categories:
			if category not in existing:
				self.append(c_field,{"name1":category})