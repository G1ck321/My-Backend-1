import time
def q():
    print("Why can't programmers tell jokes?")
    time.sleep(3)
def a():
    print("Timing!")
def main():
    q() 
    a()
# main()


import asyncio
async def q():
    print("Why can't programmers tell jokes? ")
    await asyncio.sleep(3)

async def a():
    print ("Timing!")

async def main():
    await asyncio.gather(q(),a()) 

asyncio.run(main())