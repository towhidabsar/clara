def computeDeriv(poly):
  deriv = []
  deg = 2
  for i in range(1, len(poly)):
    val = (deg-1)*poly[i]
    if val == -0.0: val = 0.0
    deriv.append(float(val))
    deg+=1
  if len(deriv) == 0:
    deriv.append(0.0)
  return deriv
