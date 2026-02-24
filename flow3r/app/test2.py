import pandas as pd
import numpy as np

pandas_nan = pd.NA
numpy_nan = np.nan

print("pd.NA", pd.NA)
print("np.nan", np.nan)
print("type(pd.NA)", type(pd.NA))
print("type(np.nan)", type(np.nan))
print("pd.NA == np.nan", pd.NA == np.nan)
print("pd.NA is np.nan", pd.NA is np.nan)
print("pd.NA == pd.NA", pd.NA == pd.NA)
print("pd.NA is pd.NA", pd.NA is pd.NA)
print("np.nan == np.nan", np.nan == np.nan)
print("np.nan is np.nan", np.nan is np.nan)