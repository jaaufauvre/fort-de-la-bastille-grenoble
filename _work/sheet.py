import sys,os,glob,math
from PIL import Image,ImageDraw,ImageFont
src=sys.argv[1]; out=sys.argv[2]; per=int(sys.argv[3]) if len(sys.argv)>3 else 20
files=sorted(f for f in glob.glob(os.path.join(src,'*')) if f.lower().endswith(('.jpg','.jpeg','.png','.webp','.gif')))
T=300; cols=5
try: font=ImageFont.truetype('arial.ttf',13)
except: font=ImageFont.load_default()
for s in range(0,len(files),per):
    chunk=files[s:s+per]; rows=math.ceil(len(chunk)/cols)
    sheet=Image.new('RGB',(cols*T,rows*(T+34)),'white'); d=ImageDraw.Draw(sheet)
    for k,f in enumerate(chunk):
        try:
            im=Image.open(f); im.thumbnail((T-6,T-6)); im=im.convert('RGB')
            x=(k%cols)*T; y=(k//cols)*(T+34)
            sheet.paste(im,(x+3,y+3))
            d.text((x+3,y+T),f'{s+k}: '+os.path.basename(f)[:40],fill='black',font=font)
            d.text((x+3,y+T+15),f'{Image.open(f).size}',fill='gray',font=font)
        except Exception as e: print('ERR',f,e)
    sheet.save(f'{out}_{s//per:02d}.jpg',quality=80)
print(len(files))
