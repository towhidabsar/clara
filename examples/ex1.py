def computeDeriv(poly):
  index = 0
  result = []
    
  while index < len(poly)-1:
    result.append(float(poly[index+1]*(index+1)))
    index += 1
    
  if len(poly) == 1:
    result.append(0.0)
    
  return result
