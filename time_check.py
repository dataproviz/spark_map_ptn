import time

start = time.time()

# your heavy function
result = heavy_function()

end = time.time()
print(f"Time taken: {end - start:.2f} seconds")