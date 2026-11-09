#!/usr/bin/env python3
"""Gera a versão pública (GitHub Pages) da Estante em Cartaz a partir do artefato.
uso: build_site.py <estante.html> <dir_db> <dir_saida>"""
import json,glob,os,sys,re
src,db,out=sys.argv[1:4]
s=open(src,encoding='utf-8').read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(a[:70],s.count(a)); s=s.replace(a,b)
def cut(a,b,new=''):
    global s
    i=s.index(a);j=s.index(b,i)+len(b);s=s[:i]+new+s[j:]
# 1) sem adição de livros
cut('  <section class="add" id="add">','  </section>\n')
cut('$("#addLink").addEventListener("input"','  if(ok)toast(`${ok} livro${ok>1?"s":""} adicionado${ok>1?"s":""} à fila`);\n});\n')
rep('''  $("#queue").textContent=''','''  if($("#queue"))$("#queue").textContent=''')
# 2) textos da cópia pública
rep('''<p>Todo dia, por volta das 19h, cada livro da sua lista ganha um registro de preço. Aqui você vê quem está mais barato, quem bateu o seu alvo e qual é a hora certa de comprar.</p>''',
    '''<p>Um registro diário de preços de livros na Amazon.com.br. Aqui você vê quem está mais barato, quem bateu o seu alvo e qual é a hora certa de comprar.</p>''')
rep('''<span class="pill">Próxima sessão ~<b>19h</b></span>''','''<span class="pill">Cópia pública · <a href="https://github.com/Zanitchy/estante-em-cartaz#readme" target="_blank" rel="noopener" style="color:var(--sun)">relatório técnico ↗</a></span>''')
# avisos pelo app do Claude não existem fora do artefato
s=re.sub(r'(<button[^>]*id="alertBtn")',r'\1 hidden',s,count=1); assert 'id="alertBtn" hidden' in s
# 3) Excel: download direto pelo navegador
rep('''  const dl=await window.claude?.use?.("downloads");if(!dl){toast("Exportar não está disponível nesta visualização");return}''',
    '''  const dl={save:async({filename,data})=>{const u=URL.createObjectURL(new Blob([data],{type:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}));const a=document.createElement("a");a.href=u;a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),5000)}};''')
# 4) dados: arquivos estáticos + marcações no navegador
cut('(async()=>{\n  const db=await window.claude?.use?.("db");','})();','''(async()=>{
  const KEY="estante-em-cartaz-prefs-v1";
  S.db={doc:()=>({set:async d=>{try{localStorage.setItem(KEY,JSON.stringify(d))}catch(e){throw{code:"storage"}}}})};
  try{const d=JSON.parse(localStorage.getItem(KEY)||"{}");S.prefs=d.itens||{};S.meta.orcamento=d.orcamento??null;S.meta.alertas={...S.meta.alertas,...(d.alertas||{})}}catch(e){}
  try{const[L,D]=await Promise.all(["data/livros.json","data/dias.json"].map(u=>fetch(u).then(r=>{if(!r.ok)throw new Error(u+" "+r.status);return r.json()})));
    const o={};L.forEach(x=>o[x.asin]=x);S.livros=o;S.dias=D.sort((a,b)=>a.data<b.data?-1:1);render()}
  catch(e){console.error(e);$("#status").innerHTML="<span class='pill'>Não consegui carregar os dados. Recarregue a página.</span>"}
})();''')
assert 'window.claude' not in s, [m.start() for m in re.finditer('window.claude',s)]
head='''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="Estante em Cartaz: histórico diário de preços de livros na Amazon.com.br, com estatísticas de promoções, editoras e autores.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%8E%AC%3C/text%3E%3C/svg%3E">
<style>:root{color-scheme:light;box-sizing:border-box}body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#fff;color:#000}img{max-width:100%}[hidden]:not([hidden=until-found i]){display:none!important}</style>
'''
i=s.index('<style>');title_links=s[:i];rest=s[i:]
k=rest.index('</style>')+8
html=head+title_links+rest[:k]+'\n</head><body>\n'+rest[k:]+'\n</body></html>\n'
os.makedirs(out+'/data',exist_ok=True)
open(out+'/index.html','w',encoding='utf-8').write(html)
# dados
L=[]
for f in sorted(glob.glob(db+'/livros/*.json')):
    d=json.load(open(f,encoding='utf-8'));a=d.get('asin') or os.path.basename(f)[:-5];d['asin']=a
    d['capa']=f'capas/{a}.jpg' if os.path.exists(f'{out}/capas/{a}.jpg') else None
    for k in ('capaUrl','adicionadoEm'): d.pop(k,None)
    L.append({k:v for k,v in d.items() if v is not None})
D=[json.load(open(f,encoding='utf-8')) for f in sorted(glob.glob(db+'/dias/*.json'))]
for d in D: d['itens']={a:it for a,it in d['itens'].items() if it}
dump=lambda o,p:open(p,'w',encoding='utf-8').write(json.dumps(o,ensure_ascii=False,separators=(',',':')))
dump(L,out+'/data/livros.json');dump(D,out+'/data/dias.json')
print(len(L),'livros,',len(D),'dias, sem capa:',[x['asin'] for x in L if not x.get('capa')][:20])
