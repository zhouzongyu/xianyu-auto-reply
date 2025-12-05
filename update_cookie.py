#!/usr/bin/env python3
"""
更新Cookie到数据库
"""

import asyncio
from db_manager import db_manager


async def update_cookie(cookie_id: str, cookie_value: str):
    """更新Cookie到数据库"""
    try:
        # 检查Cookie是否已存在
        existing_cookies = db_manager.get_all_cookies()
        
        if cookie_id in existing_cookies:
            # 更新现有Cookie
            db_manager.update_cookie_account_info(
                cookie_id=cookie_id,
                cookie_value=cookie_value
            )
            print(f"✅ 已更新Cookie: {cookie_id}")
        else:
            # 添加新Cookie - 使用save_cookie方法
            db_manager.save_cookie(
                cookie_id=cookie_id,
                cookie_value=cookie_value
            )
            print(f"✅ 已添加新Cookie: {cookie_id}")
        
        print(f"✅ Cookie更新成功！")
        return True
        
    except Exception as e:
        print(f"❌ 更新Cookie失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    # 新提供的Cookie
    new_cookie = "t=49fa19f708d1b1e126b83f1707da5df4; cna=e1mwIcRFHCYCAXAXMYd3CqPk; isg=BHNzJ5wnHjciY9Jjdpc6bAokAnedqAdqOAcjGiURyRKiJJPGrXnEutS92lTKhF9i; tracknick=xy873867389712; unb=2218782890245; havana_lgc2_77=eyJoaWQiOjIyMTg3ODI4OTAyNDUsInNnIjoiNDc4NTZlZmJiZTllNTEzYjFhMDA2OGQzZjE3YTU5MjciLCJzaXRlIjo3NywidG9rZW4iOiIxUGFhMGI0YzR3N1VMN3AxblM2aDFPQSJ9; _hvn_lgc_=77; havana_lgc_exp=1767323265778; xlly_s=1; cookie2=1674f750d3bf81da477b54dc8248ccc3; _samesite_flag_=true; sgcookie=E100ljulwJnIY47rNmucZEYCCX7lEwbpYcmrnfCCgMqmXAOL1%2Fj9UDBVRQ9aRuUsJNQ9pnuBQS13qbBi8vMZmV7VSyt%2FORGcibu2HgKMBO%2B066w%3D; csg=2b0b9f17; _tb_token_=efee8b3bb7b33; sdkSilent=1764987070106; mtop_partitioned_detect=1; _m_h5_tk=251e1fa2f1c730b7c4263825d08e9ef7_1764920573640; _m_h5_tk_enc=91c872cedecf585971aa5d2791f9f9c1; tfstk=g_qxLdNAU_f0sTR2H5blSoQt9LXlHa24oSyBjfcD57F8dJRm5om06FF0Q501gmqTwRNd3Af4jKzztJt0mZoMXmoZf6fhxMv43co_eJ7VIEkSQvsMch_oVBVxDMChxM2flxogF64m5h-nIAishVMbFTHqhCis5xw5eAMMGFtb186-avl65ntfVYMEHcG_1c68FbksfxNsfTeSaAGSkKhMhfKTu1CqFUIJO5VQ2x3xO8QeXh1nUBcbhbK6fbDxkUejwht_2PMtpmcf8LcZmjy-H5Se0mgT5om7c_ssAyP8X2idStubBzFZmu66lXa0i0ZbJdt_emh_tugWM_hQ08ZEV4jCp8Zzi-r8IdssEWc73oiOA9oxcji-UlfycfU75o0qbI1t_ue7cPIzMkqd9IRn9AYfeTLw7qMyA4LLW7f_V-k-tTYk7FuoUYhheTLw7qMreXXlxF8ZrY5.."
    
    # 从cookie中提取用户ID作为cookie_id
    cookies_dict = {}
    for cookie in new_cookie.split("; "):
        if "=" in cookie:
            key, value = cookie.split("=", 1)
            cookies_dict[key.strip()] = value.strip()
    
    # 使用unb作为cookie_id，如果没有则使用tracknick
    cookie_id = cookies_dict.get('tracknick', '新Cookie')
    
    print("="*60)
    print("更新Cookie到数据库")
    print("="*60)
    print(f"Cookie ID: {cookie_id}")
    print(f"用户ID (unb): {cookies_dict.get('unb', 'N/A')}")
    print(f"Token: {cookies_dict.get('_m_h5_tk', 'N/A')[:30]}...")
    print()
    
    # 直接更新
    await update_cookie(cookie_id, new_cookie)


if __name__ == '__main__':
    asyncio.run(main())

