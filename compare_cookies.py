#!/usr/bin/env python3
"""对比测试脚本和实际方法的Cookie解析差异"""

import asyncio
from db_manager import db_manager

# 测试脚本中的Cookie
test_cookie = "t=49fa19f708d1b1e126b83f1707da5df4; cna=e1mwIcRFHCYCAXAXMYd3CqPk; isg=BHNzJ5wnHjciY9Jjdpc6bAokAnedqAdqOAcjGiURyRKiJJPGrXnEutS92lTKhF9i; tracknick=xy873867389712; unb=2218782890245; havana_lgc2_77=eyJoaWQiOjIyMTg3ODI4OTAyNDUsInNnIjoiNDc4NTZlZmJiZTllNTEzYjFhMDA2OGQzZjE3YTU5MjciLCJzaXRlIjo3NywidG9rZW4iOiIxUGFhMGI0YzR3N1VMN3AxblM2aDFPQSJ9; _hvn_lgc_=77; havana_lgc_exp=1767323265778; xlly_s=1; cookie2=1674f750d3bf81da477b54dc8248ccc3; _samesite_flag_=true; sgcookie=E100ljulwJnIY47rNmucZEYCCX7lEwbpYcmrnfCCgMqmXAOL1%2Fj9UDBVRQ9aRuUsJNQ9pnuBQS13qbBi8vMZmV7VSyt%2FORGcibu2HgKMBO%2B066w%3D; csg=2b0b9f17; _tb_token_=efee8b3bb7b33; sdkSilent=1764987070106; mtop_partitioned_detect=1; _m_h5_tk=251e1fa2f1c730b7c4263825d08e9ef7_1764920573640; _m_h5_tk_enc=91c872cedecf585971aa5d2791f9f9c1; tfstk=g_qxLdNAU_f0sTR2H5blSoQt9LXlHa24oSyBjfcD57F8dJRm5om06FF0Q501gmqTwRNd3Af4jKzztJt0mZoMXmoZf6fhxMv43co_eJ7VIEkSQvsMch_oVBVxDMChxM2flxogF64m5h-nIAishVMbFTHqhCis5xw5eAMMGFtb186-avl65ntfVYMEHcG_1c68FbksfxNsfTeSaAGSkKhMhfKTu1CqFUIJO5VQ2x3xO8QeXh1nUBcbhbK6fbDxkUejwht_2PMtpmcf8LcZmjy-H5Se0mgT5om7c_ssAyP8X2idStubBzFZmu66lXa0i0ZbJdt_emh_tugWM_hQ08ZEV4jCp8Zzi-r8IdssEWc73oiOA9oxcji-UlfycfU75o0qbI1t_ue7cPIzMkqd9IRn9AYfeTLw7qMyA4LLW7f_V-k-tTYk7FuoUYhheTLw7qMreXXlxF8ZrY5.."

# 从数据库获取的Cookie
db_cookie = db_manager.get_cookie('xy873867389712')

print("="*60)
print("对比Cookie解析")
print("="*60)

def parse_cookies(cookie_str):
    cookies = {}
    for cookie in cookie_str.split("; "):
        if "=" in cookie:
            key, value = cookie.split("=", 1)
            cookies[key.strip()] = value.strip()
    return cookies

test_dict = parse_cookies(test_cookie)
db_dict = parse_cookies(db_cookie)

print(f"\n测试Cookie字段数: {len(test_dict)}")
print(f"数据库Cookie字段数: {len(db_dict)}")

print("\n关键字段对比:")
key_fields = ['_m_h5_tk', '_m_h5_tk_enc', 'unb', 'cookie2', '_tb_token_']
for field in key_fields:
    test_val = test_dict.get(field, '')
    db_val = db_dict.get(field, '')
    match = "✅" if test_val == db_val else "❌"
    print(f"  {match} {field}:")
    print(f"    测试: {test_val[:30]}... (长度: {len(test_val)})")
    print(f"    数据库: {db_val[:30]}... (长度: {len(db_val)})")
    if test_val != db_val:
        print(f"    ⚠️  值不匹配！")

print("\n所有字段对比:")
all_keys = set(test_dict.keys()) | set(db_dict.keys())
diff_count = 0
for key in sorted(all_keys):
    test_val = test_dict.get(key, '')
    db_val = db_dict.get(key, '')
    if test_val != db_val:
        diff_count += 1
        print(f"  ❌ {key}: 不匹配")
        print(f"     测试: {test_val[:50]}...")
        print(f"     数据库: {db_val[:50]}...")
        if key in ['x5secdata', 'x5sectag']:
            print(f"     ⚠️  这是可能导致验证失败的字段")

print(f"\n总结: 共 {diff_count} 个字段不匹配")
if diff_count == 2 and 'x5secdata' in db_dict and 'x5sectag' in db_dict:
    print("✅ 只有 x5secdata 和 x5sectag 字段不同，这些字段应该被移除")

