# coding=utf-8
from osgeo import gdal
from gdalconst import *
import time


def readImage(img_path):
    band_data = []
    band_name = []

    # 以只读方式打开遥感影像
    dataset = gdal.Open(img_path, GA_ReadOnly)
    if dataset is None:
        print("Unable to open image file.")
        return band_data
    else:
        print("Open image file success.\n")

        # 读取地理变换参数
        param_geoTransform = dataset.GetGeoTransform()
        print "GeoTransform info:\n", param_geoTransform, "\n"

        # 读取投影信息
        param_proj = dataset.GetProjection()
        print "Projection info:\n", param_proj, "\n"

        # 读取波段数及影像大小
        bands_num = dataset.RasterCount
        print("Image height:" + dataset.RasterYSize.__str__() + " Image width:" + dataset.RasterXSize.__str__())
        print(bands_num.__str__() + " bands in total.")

        # 依次读取波段数据
        for i in range(bands_num):
            # 获取影像的第i+1个波段
            band_i = dataset.GetRasterBand(i + 1)

            # 获取影像第i+1个波段的描述(名称)
            name = band_i.GetDescription()
            band_name.append(name)

            # 读取第i+1个波段数据
            data = band_i.ReadAsArray(0, 0, band_i.XSize, band_i.YSize)
            band_data.append(data)

            print("band " + (i + 1).__str__() + " read success.")
            if name != "":
                print "Name:", name
        return band_data, param_geoTransform, param_proj, band_name


def writeImage(save_path, bands, geotrans=None, proj=None, names=None):
    projection = [
        # WGS84坐标系(EPSG:4326)
        """GEOGCS["WGS 84", DATUM["WGS_1984", SPHEROID["WGS 84", 6378137, 298.257223563, AUTHORITY["EPSG", "7030"]], AUTHORITY["EPSG", "6326"]], PRIMEM["Greenwich", 0, AUTHORITY["EPSG", "8901"]], UNIT["degree", 0.01745329251994328, AUTHORITY["EPSG", "9122"]], AUTHORITY["EPSG", "4326"]]""",
        # Pseudo-Mercator、球形墨卡托或Web墨卡托(EPSG:3857)
        """PROJCS["WGS 84 / Pseudo-Mercator",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Mercator_1SP"],PARAMETER["central_meridian",0],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["X",EAST],AXIS["Y",NORTH],EXTENSION["PROJ4","+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext  +no_defs"],AUTHORITY["EPSG","3857"]]"""
    ]

    if bands is None or bands.__len__() == 0:
        return False
    else:
        # 认为各波段大小相等，所以以第一波段信息作为保存
        band1 = bands[0]
        # 设置影像保存大小、波段数
        img_width = band1.shape[1]
        img_height = band1.shape[0]
        num_bands = bands.__len__()

        # 设置保存影像的数据类型
        if 'int8' in band1.dtype.name:
            datatype = gdal.GDT_Byte
        elif 'int16' in band1.dtype.name:
            datatype = gdal.GDT_UInt16
        else:
            datatype = gdal.GDT_Float32

        # 创建文件
        driver = gdal.GetDriverByName("GTiff")
        dataset = driver.Create(save_path, img_width, img_height, num_bands, datatype)

        if dataset is not None:
            # 写入仿射变换参数
            if geotrans is not None:
                dataset.SetGeoTransform(geotrans)

            # 写入投影参数
            if proj is not None:
                if proj is 'WGS84' or \
                        proj is 'wgs84' or \
                        proj is 'EPSG:4326' or \
                        proj is 'EPSG-4326' or \
                        proj is '4326':
                    dataset.SetProjection(projection[0])  # 写入投影
                elif proj is 'EPSG:3857' or \
                        proj is 'EPSG-3857' or \
                        proj is '3857':
                    dataset.SetProjection(projection[1])  # 写入投影
                else:
                    dataset.SetProjection(proj)  # 写入投影

            # 逐波段写入数据
            for i in range(bands.__len__()):
                raster_band = dataset.GetRasterBand(i + 1)

                # 设置没有数据的像素值为0
                raster_band.SetNoDataValue(0)

                if names is not None:
                    # 设置波段的描述(名称)
                    raster_band.SetDescription(names[i])

                # 写入数据
                raster_band.WriteArray(bands[i])
            print("save image success.")
            writeHdr(save_path, bands, geotrans, proj, names)
            return True


def writeHdr(save_path, bands, geotrans=None, proj=None, names=None):
    width = int(bands[0].shape[1])
    height = int(bands[0].shape[0])

    str_lines = "ENVI\ndescription={\n  GEO-TIFF File Imported into ENVI "
    localtime = "[" + time.strftime("%a %b %d %H:%M:%S %Y", time.localtime()) + "]}\n"
    samples = "samples = " + width.__str__() + "\n"
    lines = "lines = " + height.__str__() + "\n"
    bands = "bands = " + len(bands).__str__() + "\n"
    header_offset = "header offset = 0\n"
    file_type = "file type = TIFF\n"
    data_type = "data type = 1\n"

    others = """interleave = bip
sensor type = Unknown
byte order = 0
read procedures = {idl_tiff_read_spatial, idl_tiff_read_spectral}
coordinate system string = {GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]}
wavelength units = Unknown
data ignore value = 0
map points = {"""

    # 构造并计算影像四角点经纬度
    map_points1 = "\n 1.0000, 1.0000, " + geotrans[0].__str__() + ", " + geotrans[3].__str__() + ",\n"
    map_points2 = " " + (width + 1.0).__str__() + ", 1.0000, " + geotrans[0].__str__() + ", " + (
            height * geotrans[5] + geotrans[3]).__str__() + ",\n"
    map_points3 = " 1.0000, " + (height + 1.0).__str__() + ", " + (
            geotrans[0] + width * geotrans[1]).__str__() + ", " + geotrans[3].__str__() + ",\n"
    map_points4 = " " + (width + 1.0).__str__() + ", " + (height + 1.0).__str__() + ", " + (
            geotrans[0] + width * geotrans[1]).__str__() + ", " + geotrans[3].__str__() + "}\n"

    # 依次输出波段名
    if names is not None:
        band_names = "band names = {\n"
        for i in range(len(names)):
            band_names += names[i] + ", "
    band_names = band_names[:-2] + "}\n"

    # 拼接字符串
    str_lines += localtime
    str_lines += samples
    str_lines += lines
    str_lines += bands
    str_lines += header_offset
    str_lines += file_type
    str_lines += data_type
    str_lines += others
    str_lines += map_points1
    str_lines += map_points2
    str_lines += map_points3
    str_lines += map_points4
    str_lines += band_names

    # 保存文件
    path = save_path.split(".")[0] + ".hdr"
    output = open(path, 'w')
    output.write(str_lines)
    output.close()
    print "save hdr file success."


if __name__ == '__main__':
    # 读取影像
    data, geo, prj, name = readImage("geoImage.tif")

    # 修改名称
    for i in range(len(name)):
        name[i] = "This is band " + i.__str__().zfill(2)

    # 输出影像
    writeImage("out.tif", data, geo, prj, name)
