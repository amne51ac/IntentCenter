/**
 * IntentCenter static docs — builds left navigation from DOCS_NAV.
 * Each doc page sets <body class="docs-page" data-docs-page="api">.
 */
(function () {
  var SECTIONS = [
    {
      title: "Start here",
      items: [
        { id: "documentation", href: "documentation.html", label: "Documentation home" },
        { id: "getting-started", href: "getting-started.html", label: "Getting started" },
      ],
    },
    {
      title: "API & platform",
      items: [
        { id: "api", href: "api.html", label: "REST & OpenAPI" },
        { id: "platform", href: "platform.html", label: "Web UI & endpoints" },
        { id: "deployment", href: "deployment.html", label: "Deployment & env" },
      ],
    },
    {
      title: "Architecture",
      items: [
        { id: "architecture", href: "architecture.html", label: "Diagrams" },
        { id: "roadmap", href: "roadmap.html", label: "Vision & roadmap" },
      ],
    },
    {
      title: "Data model",
      items: [{ id: "data-model", href: "data-model.html", label: "Schema reference" }],
    },
  ];

  function currentId() {
    return document.body.getAttribute("data-docs-page") || "";
  }

  function pathMatches(href) {
    var path = window.location.pathname || "";
    var file = href.split("/").pop() || "";
    return path.endsWith(file) || path.endsWith(file + "/");
  }

  function render() {
    var host = document.getElementById("docs-sidebar");
    if (!host) return;

    var nav = document.createElement("nav");
    nav.className = "docs-nav-tree";
    nav.setAttribute("aria-label", "Documentation sections");

    var active = currentId();

    SECTIONS.forEach(function (sec) {
      var wrap = document.createElement("div");
      wrap.className = "docs-nav-section";
      var t = document.createElement("div");
      t.className = "docs-nav-title";
      t.textContent = sec.title;
      wrap.appendChild(t);
      var ul = document.createElement("ul");
      sec.items.forEach(function (item) {
        var li = document.createElement("li");
        var a = document.createElement("a");
        a.href = item.href;
        a.textContent = item.label;
        a.setAttribute("data-docs-id", item.id);
        if (active === item.id || (!active && pathMatches(item.href))) {
          a.classList.add("is-active");
        }
        li.appendChild(a);
        ul.appendChild(li);
      });
      wrap.appendChild(ul);
      nav.appendChild(wrap);
    });

    var meta = document.createElement("div");
    meta.className = "docs-nav-meta";
    meta.innerHTML =
      '<a href="index.html">← Product landing</a> · <a href="index.html#about">About</a><br />' +
      '<a href="https://demo.intentcenter.io" rel="noopener noreferrer" target="_blank">Live demo</a><br />' +
      '<a class="github-inline" href="https://github.com/amne51ac/intentcenter" rel="noopener noreferrer" target="_blank">' +
      '<img class="github-mark-inline" src="assets/github-mark.svg" width="16" height="16" alt="" aria-hidden="true" />' +
      '<span>Repository on GitHub</span></a>';

    host.appendChild(nav);
    host.appendChild(meta);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render);
  } else {
    render();
  }
})();
