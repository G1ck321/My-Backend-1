const revealElements = document.querySelectorAll('.reveal, .reveal-delay')

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible')
        observer.unobserve(entry.target)
      }
    })
  },
  {
    threshold: 0.2,
    rootMargin: '0px 0px -40px 0px',
  }
)

revealElements.forEach((element) => observer.observe(element))

const yearNode = document.querySelector('[data-year]')
if (yearNode) {
  yearNode.textContent = String(new Date().getFullYear())
}
