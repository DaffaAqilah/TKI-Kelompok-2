const PER_PAGE = 6;

let currentPage = 1;
let totalPages = 1;

const $ = id => document.getElementById(id);

/* DATA CONTOH UNTUK FRONTEND */
const MOCK_NEWS = [
  {
    id:1,
    category:"POLITICS",
    headline:"How Climate Policy Is Reshaping the Global Energy Debate",
    authors:"Maya Thompson",
    link:"",
    short_description:"A closer look at how governments are balancing energy security, economic growth, and long-term climate commitments.",
    date:"2022-11-18"
  },
  {
    id:2,
    category:"BUSINESS",
    headline:"Small Businesses Turn to Digital Tools to Reach New Customers",
    authors:"Daniel Brooks",
    link:"",
    short_description:"Independent businesses are adopting online platforms, data tools, and digital payments.",
    date:"2022-08-07"
  },
  {
    id:3,
    category:"TECH",
    headline:"What the Next Generation of Computing Could Mean for Everyday Life",
    authors:"Alicia Morgan",
    link:"",
    short_description:"Researchers and technology companies are exploring faster and more efficient systems.",
    date:"2022-06-12"
  },
  {
    id:4,
    category:"ENTERTAINMENT",
    headline:"The Films and Performances That Defined This Year's Conversation",
    authors:"Jordan Lee",
    link:"",
    short_description:"Stories from independent cinema to major studio releases.",
    date:"2021-12-21"
  },
  {
    id:5,
    category:"WELLNESS",
    headline:"Building a Healthier Daily Routine Starts With Small Habits",
    authors:"Sarah Wilson",
    link:"",
    short_description:"Experts explain why consistent sleep, movement, and realistic goals matter.",
    date:"2021-09-03"
  },
  {
    id:6,
    category:"TRAVEL",
    headline:"A Guide to Exploring Local Destinations More Responsibly",
    authors:"Nadia Rahman",
    link:"",
    short_description:"Travelers are looking for meaningful experiences while supporting local communities.",
    date:"2021-05-16"
  },
  {
    id:7,
    category:"SPORTS",
    headline:"How Data Analytics Is Changing the Way Teams Prepare for Games",
    authors:"Chris Evans",
    link:"",
    short_description:"Coaches and analysts are using performance data to understand player development.",
    date:"2020-10-28"
  },
  {
    id:8,
    category:"FOOD & DRINK",
    headline:"Why Home Cooking Became a New Creative Outlet",
    authors:"Emily Carter",
    link:"",
    short_description:"Home cooks are experimenting with regional recipes and simple ingredients.",
    date:"2020-07-09"
  },
  {
    id:9,
    category:"SCIENCE",
    headline:"New Research Explores the Future of Clean Energy",
    authors:"Olivia Green",
    link:"",
    short_description:"Scientists are investigating ways to improve energy efficiency.",
    date:"2019-11-14"
  },
  {
    id:10,
    category:"PARENTING",
    headline:"Helping Children Build Healthy Relationships With Technology",
    authors:"Rebecca Hall",
    link:"",
    short_description:"Families and educators share approaches to screen time and online safety.",
    date:"2019-04-22"
  },
  {
    id:11,
    category:"COMEDY",
    headline:"The Internet Moments That Brought People Together",
    authors:"Alex Rivera",
    link:"",
    short_description:"A collection of light-hearted stories and creative online moments.",
    date:"2018-08-30"
  },
  {
    id:12,
    category:"HEALTHY LIVING",
    headline:"Understanding the Connection Between Sleep and Focus",
    authors:"Priya Shah",
    link:"",
    short_description:"Sleep researchers describe how regular rest supports memory and concentration.",
    date:"2017-03-11"
  }
];

/* AMBIL FILTER */
function getFilters(){
  return {
    q:$("queryInput").value.trim(),
    category:$("category").value,
    year_from:$("yearFrom").value,
    year_to:$("yearTo").value,
    author:$("author").value.trim(),
    page:currentPage,
    per_page:PER_PAGE
  };
}

/* SUSUN URL API */
function buildURL(filters){
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key,value])=>{
    if(value !== "" && value !== null && value !== undefined){
      params.set(key,value);
    }
  });

  return `/search?${params.toString()}`;
}

/* NORMALISASI DATA API */
function normalizeArticle(item,index){
  return {
    id:item.id ?? item.doc_id ?? index,
    category:item.category ?? "UNCATEGORIZED",
    headline:item.headline ?? item.title ?? "Tanpa judul",
    authors:Array.isArray(item.authors)
      ? item.authors.join(", ")
      : (item.authors || "Penulis tidak diketahui"),
    link:item.link ?? item.url ?? "",
    short_description:item.short_description ?? item.description ?? "",
    date:item.date ?? ""
  };
}

/* FILTER DATA SIMULASI */
function filterMock(filters){
  let data = [...MOCK_NEWS];

  const q = filters.q.toLowerCase();
  const category = filters.category.toLowerCase();
  const author = filters.author.toLowerCase();

  // Fallback sederhana, bukan parser Boolean lengkap.
  const excluded = [...q.matchAll(/\bNOT\s+([\w'-]+)/g)]
    .map(m=>m[1]);

  const cleaned = q
    .replace(/\bNOT\s+[\w'-]+/g," ")
    .replace(/\b(AND|OR|NOT)\b/g," ")
    .replace(/[()]/g," ");

  const terms = cleaned.split(/\s+/).filter(Boolean);
  const useOR = /\bOR\b/i.test(q);

  if(terms.length){
    data = data.filter(article=>{
      const text = (
        article.headline + " " + article.category
      ).toLowerCase();

      const matched = useOR
        ? terms.some(term=>text.includes(term))
        : terms.every(term=>text.includes(term));

      const blocked = excluded.some(term=>text.includes(term));

      return matched && !blocked;
    });
  }

  if(category){
    data = data.filter(a=>a.category.toLowerCase()===category);
  }

  if(filters.year_from){
    data = data.filter(a=>
      Number(a.date.substring(0,4)) >= Number(filters.year_from)
    );
  }

  if(filters.year_to){
    data = data.filter(a=>
      Number(a.date.substring(0,4)) <= Number(filters.year_to)
    );
  }

  if(author){
    data = data.filter(a=>
      a.authors.toLowerCase().includes(author)
    );
  }

  const total = data.length;
  const pages = Math.max(1,Math.ceil(total/PER_PAGE));
  const start = (filters.page-1)*PER_PAGE;

  return {
    results:data.slice(start,start+PER_PAGE),
    total,
    page:filters.page,
    total_pages:pages
  };
}

/* REQUEST KE FLASK */
async function requestSearch(filters){
  const response = await fetch(buildURL(filters),{
    method:"GET",
    headers:{"Accept":"application/json"}
  });

  if(!response.ok){
    throw new Error("HTTP "+response.status);
  }

  const payload = await response.json();

  const list = Array.isArray(payload)
    ? payload
    : (payload.results ?? payload.data ?? []);

  return {
    results:list.map(normalizeArticle),
    total:Number(payload.total ?? list.length),
    page:Number(payload.page ?? filters.page),
    total_pages:Number(
      payload.total_pages ??
      Math.max(1,Math.ceil(Number(payload.total ?? list.length)/PER_PAGE))
    )
  };
}

/* ESCAPE HTML UNTUK MENCEGAH HTML INJECTION */
function escapeHTML(value){
  return String(value ?? "").replace(/[&<>"']/g,char=>({
    "&":"&amp;",
    "<":"&lt;",
    ">":"&gt;",
    '"':"&quot;",
    "'":"&#39;"
  }[char]));
}

/* HIGHLIGHT KATA KUNCI */
function highlight(text,query){
  let safe = escapeHTML(text);

  const words = query
    .replace(/[()]/g," ")
    .replace(/\b(AND|OR|NOT)\b/gi," ")
    .match(/[\p{L}\p{N}'-]+/gu) || [];

  const unique = [...new Set(words)].sort((a,b)=>b.length-a.length);

  if(!unique.length) return safe;

  const pattern = unique
    .map(w=>w.replace(/[.*+?^${}()|[\]\\]/g,"\\$&"))
    .join("|");

  return safe.replace(
    new RegExp(`(${pattern})`,"gi"),
    "<mark>$1</mark>"
  );
}

/* FORMAT TANGGAL */
function formatDate(value){
  if(!value) return "Tanggal tidak tersedia";

  const date = new Date(value);

  if(Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("id-ID",{
    day:"numeric",
    month:"short",
    year:"numeric"
  }).format(date);
}

/* LINK BERITA */
function articleLink(article){
  if(article.link && /^https?:\/\//i.test(article.link)){
    return `<a class="read" href="${escapeHTML(article.link)}"
      target="_blank" rel="noopener noreferrer">Baca berita ↗</a>`;
  }

  return `<span class="author">Arsip HuffPost</span>`;
}

/* RENDER BERITA */
function renderResults(data,query){
  const container = $("results");
  container.innerHTML = "";

  $("resultCount").textContent =
    data.total.toLocaleString("id-ID")+" artikel ditemukan";

  $("resultHeading").textContent = query
    ? `Hasil pencarian: "${query}"`
    : "Artikel populer";

  $("empty").style.display = data.results.length ? "none":"block";

  if(data.results.length){
    const articles = data.results;

    const lead = articles[0];

    const leadHTML = `
      <article class="lead">
        <div class="lead-art">${escapeHTML(lead.category[0] || "N")}</div>
        <div class="meta">
          NusaNews · ${escapeHTML(lead.category)}
          · ${escapeHTML(formatDate(lead.date))}
        </div>
        <h3>${highlight(lead.headline,query)}</h3>
        <p>${highlight(lead.short_description,query)}</p>
        <div class="author">Oleh ${escapeHTML(lead.authors)}</div>
        ${articleLink(lead)}
      </article>
    `;

    const relatedHTML = articles.slice(1,4).map(article=>`
      <article>
        <div class="meta">
          NusaNews · ${escapeHTML(article.category)}
          · ${escapeHTML(formatDate(article.date))}
        </div>
        <h3>${highlight(article.headline,query)}</h3>
        <p>${highlight(article.short_description,query)}</p>
        <div class="author">${escapeHTML(article.authors)}</div>
        ${articleLink(article)}
      </article>
    `).join("");

    container.innerHTML = `
      <div class="stories">
        ${leadHTML}
        <div class="related">${relatedHTML}</div>
      </div>
    `;

    const remaining = articles.slice(4);

    if(remaining.length){
      const more = document.createElement("div");
      more.className = "more";

      more.innerHTML = remaining.map(article=>`
        <article>
          <div class="more-copy">
            <div class="meta">
              ${escapeHTML(article.category)}
              · ${escapeHTML(formatDate(article.date))}
            </div>
            <h3>${highlight(article.headline,query)}</h3>
            <p>${highlight(article.short_description,query)}</p>
            <div class="author">Oleh ${escapeHTML(article.authors)}</div>
            ${articleLink(article)}
          </div>
          <div class="more-mark">${escapeHTML(article.category[0] || "N")}</div>
        </article>
      `).join("");

      container.appendChild(more);
    }
  }

  currentPage = Math.max(1,data.page);
  totalPages = Math.max(1,data.total_pages);

  $("pagination").hidden = data.total === 0;
  $("prev").disabled = currentPage <= 1;
  $("next").disabled = currentPage >= totalPages;

  $("pageInfo").textContent =
    `Halaman ${currentPage} dari ${totalPages}`;
}

/* FUNGSI UTAMA PENCARIAN */
async function runSearch(){
  const filters = getFilters();

  const from = Number(filters.year_from);
  const to = Number(filters.year_to);

  if(from && to && from > to){
    alert("Tahun dari tidak boleh lebih besar dari tahun sampai.");
    return;
  }

  $("loading").style.display = "block";
  $("results").style.display = "none";
  $("empty").style.display = "none";

  try{
    const data = await requestSearch(filters);

    $("status").textContent = "● Terhubung ke API";
    $("status").className = "status";

    renderResults(data,filters.q);

  }catch(error){
    console.warn("API belum tersedia, menggunakan data contoh:",error);

    const data = filterMock(filters);

    $("status").textContent = "● Data contoh";
    $("status").className = "status mock";

    renderResults(data,filters.q);

  }finally{
    $("loading").style.display = "none";
    $("results").style.display = "block";
  }
}

/* EVENT PENCARIAN */
$("searchForm").addEventListener("submit",event=>{
  event.preventDefault();
  currentPage = 1;
  runSearch();
});

/* EVENT FILTER */
$("filterForm").addEventListener("submit",event=>{
  event.preventDefault();
  currentPage = 1;
  runSearch();
});

/* RESET FILTER */
$("reset").addEventListener("click",()=>{
  $("queryInput").value = "";
  $("category").value = "";
  $("yearFrom").value = "";
  $("yearTo").value = "";
  $("author").value = "";

  currentPage = 1;
  runSearch();
});

/* PAGINATION */
$("prev").addEventListener("click",()=>{
  if(currentPage > 1){
    currentPage--;
    runSearch();
  }
});

$("next").addEventListener("click",()=>{
  if(currentPage < totalPages){
    currentPage++;
    runSearch();
  }
});

/* NAVIGASI KATEGORI */
document.querySelectorAll(".nav a[data-category]").forEach(link=>{
  link.addEventListener("click",event=>{
    event.preventDefault();

    $("category").value = link.dataset.category;
    currentPage = 1;

    document.querySelectorAll(".nav a").forEach(a=>
      a.classList.remove("active")
    );

    link.classList.add("active");
    runSearch();
  });
});

/* TOPIK PILIHAN */
document.querySelectorAll(".side-item[data-category]").forEach(item=>{
  item.style.cursor = "pointer";

  item.addEventListener("click",()=>{
    $("category").value = item.dataset.category;
    currentPage = 1;
    runSearch();

    $("hasil").scrollIntoView({behavior:"smooth"});
  });
});

/* JALANKAN SAAT HALAMAN DIBUKA */
runSearch();