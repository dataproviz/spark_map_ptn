import os
import tempfile

def stream_s3a_to_local(s3a_path: str, local_path: str, buf_size=16 * 1024 * 1024):
    jvm = spark._jvm
    hconf = spark.sparkContext._jsc.hadoopConfiguration()

    jpath = jvm.org.apache.hadoop.fs.Path(s3a_path)
    fs = jpath.getFileSystem(hconf)
    inp = fs.open(jpath)

    try:
        with open(local_path, "wb") as out:
            b = jvm.java.lang.reflect.Array.newInstance(jvm.java.lang.Byte.TYPE, buf_size)
            while True:
                n = inp.read(b, 0, buf_size)
                if n == -1:
                    break
                out.write(bytes(bytearray(b[:n])))
    finally:
        inp.close()