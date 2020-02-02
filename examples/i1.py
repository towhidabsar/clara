def computeDeriv(poly):
  new = []
  for i in xrange(1,len(poly)):
    new.append(
        float(i*poly[i]))
  if new==[]:
    return 0.0
  return new
