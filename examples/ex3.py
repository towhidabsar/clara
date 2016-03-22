def computeDeriv(poly):
  deriv = []
  m = 0
  while m < len(poly) + 1:
    if(m == 0):
      deriv.append(poly[1])
    else:
      deriv.append(poly[m+1]*(m+1))
    m = m + 1
    
  if deriv == []:
    deriv.append(0.0)
    
  return deriv
