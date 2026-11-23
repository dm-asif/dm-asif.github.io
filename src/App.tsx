import { useEffect, useRef, useState, type PointerEvent as ReactPointerEvent, type ReactNode } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowUpRight, BookOpen, ChevronRight, Code2, Download, ExternalLink, GraduationCap, Mail, MapPin, Menu, Sparkles, X } from 'lucide-react';

type Page = 'home' | 'about' | 'skills' | 'projects' | 'education' | 'activities' | 'contact';
const pageMeta: Record<Page, { label: string; eyebrow: string; title: string }> = {
  home: { label: 'Home', eyebrow: 'Portfolio / 2026', title: 'Building a thoughtful foundation in software.' },
  about: { label: 'About', eyebrow: 'A little context', title: 'Curious by nature. Intentional by practice.' },
  skills: { label: 'Skills', eyebrow: 'My toolkit', title: 'A growing set of engineering fundamentals.' },
  projects: { label: 'Projects', eyebrow: 'Selected work', title: 'Small ideas, made tangible.' },
  education: { label: 'Education', eyebrow: 'The journey so far', title: 'Learning with purpose and consistency.' },
  activities: { label: 'Activities', eyebrow: 'Outside the classroom', title: 'Showing up for the community around me.' },
  contact: { label: 'Contact', eyebrow: 'Let’s connect', title: 'Open to thoughtful conversations.' },
};
const navItems: { key: Page; label: string }[] = [
  { key: 'home', label: 'Home' }, { key: 'about', label: 'About' }, { key: 'skills', label: 'Skills' },
  { key: 'projects', label: 'Projects' }, { key: 'education', label: 'Education' }, { key: 'activities', label: 'Activities' }, { key: 'contact', label: 'Contact' },
];
const MotionSection = ({ children, className = '' }: { children: ReactNode; className?: string }) => (
  <motion.section initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: '-80px' }} transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }} className={className}>{children}</motion.section>
);

function trackGlassPointer(event: ReactPointerEvent<HTMLElement>) {
  if (event.pointerType === 'touch') return;
  const element = event.currentTarget;
  const rect = element.getBoundingClientRect();
  const x = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
  const y = Math.max(0, Math.min(1, (event.clientY - rect.top) / rect.height));
  element.style.setProperty('--glass-x', `${x * 100}%`);
  element.style.setProperty('--glass-y', `${y * 100}%`);
  element.dataset.glassActive = 'true';
}

function resetGlassPointer(event: ReactPointerEvent<HTMLElement>) {
  event.currentTarget.dataset.glassActive = 'false';
}

function App() {
  const [page, setPage] = useState<Page>(() => { const hash = window.location.hash.slice(2) as Page; return pageMeta[hash] ? hash : 'home'; });
  const [menuOpen, setMenuOpen] = useState(false);
  const [welcomeOpen, setWelcomeOpen] = useState(false);
  const headerRef = useRef<HTMLElement>(null);
  const activeNavRef = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const header = headerRef.current;
    if (!header || !window.liquidGlass) return;
    const glass = window.liquidGlass(header, { scale: -48, chroma: 2, border: 0.13, mapBlur: 9, blur: 5, saturate: 1.25, fallbackBlur: 15 });
    return () => glass.destroy();
  }, []);
  useEffect(() => {
    const indicator = activeNavRef.current;
    if (!indicator || !window.liquidGlass) return;
    const glass = window.liquidGlass(indicator, { scale: -30, chroma: 1, border: .2, mapBlur: 6, blur: 6, saturate: 1.45, radius: 13, fallbackBlur: 12 });
    return () => glass.destroy();
  }, [page]);
  useEffect(() => {
    if (!sessionStorage.getItem('portfolio-welcomed')) setWelcomeOpen(true);
    const onHashChange = () => { const next = window.location.hash.slice(2) as Page; setPage(pageMeta[next] ? next : 'home'); setMenuOpen(false); window.scrollTo({ top: 0, behavior: 'instant' }); };
    window.addEventListener('hashchange', onHashChange); return () => window.removeEventListener('hashchange', onHashChange);
  }, []);
  const navigate = (next: Page) => { window.location.hash = `/${next}`; };
  return <div className="site-shell">
    <div className="grain" aria-hidden="true" />
    <header className="site-header" ref={headerRef} onPointerMove={trackGlassPointer} onPointerLeave={resetGlassPointer}>
      <button className="wordmark" onClick={() => navigate('home')} aria-label="Go to home"><span className="wordmark-mark">A</span><span>MD. ASIF HOSSAIN</span></button>
      <nav className={`main-nav ${menuOpen ? 'is-open' : ''}`} aria-label="Main navigation">
        {navItems.map((item) => <button key={item.key} className={page === item.key ? 'active' : ''} onClick={() => navigate(item.key)} aria-current={page === item.key ? 'page' : undefined}><span className="nav-label">{item.label}</span>{page === item.key && <motion.span ref={activeNavRef} layoutId="liquid-nav-active-pill" className="nav-liquid-indicator" transition={{ type: 'spring', stiffness: 340, damping: 30 }} />}</button>)}
      </nav>
      <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle menu">{menuOpen ? <X size={20} /> : <Menu size={20} />}</button>
    </header>
    <main><AnimatePresence mode="wait"><motion.div key={page} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
      {page === 'home' && <Home navigate={navigate} />} {page === 'about' && <About navigate={navigate} />} {page === 'skills' && <Skills />} {page === 'projects' && <Projects />} {page === 'education' && <Education />} {page === 'activities' && <Activities />} {page === 'contact' && <Contact />}
    </motion.div></AnimatePresence></main>
    <footer className="site-footer"><span>© {new Date().getFullYear()} MD. ASIF HOSSAIN</span><span></span></footer>
    <AnimatePresence>{welcomeOpen && <WelcomeModal onClose={() => { sessionStorage.setItem('portfolio-welcomed', '1'); setWelcomeOpen(false); }} onExplore={() => { sessionStorage.setItem('portfolio-welcomed', '1'); setWelcomeOpen(false); navigate('about'); }} />}</AnimatePresence>
  </div>;
}
function PageIntro({ page, children }: { page: Page; children?: ReactNode }) { return <div className="page-intro"><p className="eyebrow">{pageMeta[page].eyebrow}</p><h1>{pageMeta[page].title}</h1>{children}</div>; }
function Home({ navigate }: { navigate: (page: Page) => void }) {
  return <div className="home-page"><section className="hero"><div className="hero-copy">
    <motion.p className="eyebrow" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: .2 }}>Software Engineering / Student</motion.p>
    <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: .3, duration: .8 }}>MD. ASIF<br /><em>HOSSAIN</em></motion.h1>
    <motion.p className="hero-lede" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: .65 }}>Learning to turn clear thinking into useful software — one considered step at a time.</motion.p>
    <motion.div className="button-row" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: .8 }}><button className="button button-primary" onClick={() => navigate('projects')}>Explore my work <ArrowUpRight size={16} /></button><button className="button button-ghost" onClick={() => navigate('about')}>About me <ChevronRight size={16} /></button></motion.div>
    <motion.div className="hero-socials" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1 }} aria-label="Social and contact links">
      <a className="icon-link" href="mailto:dmasif.me@gmail.com" aria-label="Email Asif"><Mail size={17} /></a><a className="icon-link" href="https://github.com/dm-asif" target="_blank" rel="noreferrer" aria-label="GitHub"><Code2 size={17} /></a><a className="icon-link" href="https://www.linkedin.com/in/dmasif143/" target="_blank" rel="noreferrer" aria-label="LinkedIn"><span className="social-letter">in</span></a><a className="icon-link" href="https://facebook.com/dmasif.me" target="_blank" rel="noreferrer" aria-label="Facebook"><span className="social-letter">f</span></a>
      <span className="hero-social-label">Connect</span>
    </motion.div>
  </div><div className="hero-art"><div className="hero-cv"><a className="button button-primary" href="/assets/MD_Asif_Hossain_CV.pdf" target="_blank" rel="noreferrer">View CV <ExternalLink size={15} /></a><a className="button button-ghost" href="/assets/MD_Asif_Hossain_CV.pdf" download>Download CV <Download size={15} /></a></div><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="orbit-core"><span>01</span><span>curiosity</span></div><div className="hero-note">Based in Dhaka<br /><span>Bangladesh</span></div></div></section>
  <MotionSection className="home-strip"><span className="strip-label">Currently</span><span className="strip-line" /><span>Studying Software Engineering at Green University of Bangladesh</span></MotionSection></div>;
}
function About({ navigate }: { navigate: (page: Page) => void }) {
  return <div className="page"><PageIntro page="about"><p className="intro-copy">I’m a Software Engineering student who enjoys understanding how things work — then building them a little better.</p></PageIntro>
    <MotionSection className="about-grid"><div className="section-index">01 <span>Profile</span></div><div className="about-body"><p>My interest in technology started with a simple curiosity: how can a set of instructions become something people use every day? At Green University of Bangladesh, I’m developing the fundamentals to answer that question with care — from programming and object-oriented thinking to databases and software design.</p><p>I’m still early in the journey, and I value that. Every project is an opportunity to ask better questions, practice the details, and become a more reliable engineer.</p><div className="about-signoff">MD. ASIF HOSSAIN <span>— Software Engineering Student</span></div></div></MotionSection>
    <MotionSection className="ambition-card"><Sparkles size={20} /><div><p className="eyebrow">Looking ahead</p><h2>Building for the long term.</h2><p>My ambition is to grow into a strong software engineer at a leading global technology company, then use that experience to establish and grow my own software or IT company.</p><button className="text-link" onClick={() => navigate('contact')}>Start a conversation <ArrowUpRight size={15} /></button></div></MotionSection></div>;
}
function Skills() {
  const skills = [['01', 'C Programming', 'Problem solving & fundamentals'], ['02', 'C++ Programming', 'Problem solving & fundamentals'],['03', 'Java', 'Object-oriented foundations'], ['04', 'Object-Oriented Programming', 'Thinking in systems'], ['05', 'MySQL', 'Working with structured data'], ['06', 'Basic MS Office', 'Everyday productivity']];
  return <div className="page"><PageIntro page="skills"><p className="intro-copy">The fundamentals I’m investing in now — with room to keep growing.</p></PageIntro><MotionSection className="skills-list">{skills.map(([number, name, detail]) => <div className="skill-row" key={name}><span className="skill-number">{number}</span><h2>{name}</h2><span className="skill-detail">{detail}</span></div>)}</MotionSection></div>;
}
function Projects() {
  const projects = [
    { number: '01', title: 'HerCare', desc: 'A women’s health tracking Android application designed around a more considered, private experience.', tags: ['Android'], accent: 'rose', href: 'https://github.com/dm-asif/HerCare', logo: '/assets/projects/hercare-logo.jpg' },
    { number: '02', title: 'Student OS', desc: 'A university life and academic organization application concept for bringing everyday student tasks into one place.', tags: ['Android'], accent: 'sand', href: 'https://github.com/dm-asif/Student-OS', logo: '/assets/projects/student-os-logo.jpg' },
  ];
  return <div className="page"><PageIntro page="projects"><p className="intro-copy">Two project directions shaped by real student needs.</p></PageIntro><div className="project-grid">{projects.map((project) => <MotionSection className={`project-card ${project.accent}`} key={project.title}><a className="project-card-link" href={project.href} target="_blank" rel="noreferrer" aria-label={`Open ${project.title} GitHub repository`}><div className="project-visual project-visual-logo"><span className="project-number">{project.number}</span><div className="project-logo-frame"><img src={project.logo} alt={`${project.title} app logo`} loading="lazy" /></div><span className="project-logo-caption">Official app logo</span></div><div className="project-info"><div className="project-meta"><span>Selected project</span>{project.tags.map(tag => <span key={tag}>{tag}</span>)}</div><h2>{project.title}</h2><p>{project.desc}</p><span className="project-status">View GitHub repository <ArrowUpRight size={15} /></span></div></a></MotionSection>)}</div></div>;
}
function Education() {
  return <div className="page"><PageIntro page="education"><p className="intro-copy">A record of steady progress, inside and outside the classroom.</p></PageIntro><div className="education-layout"><MotionSection className="education-main"><div className="timeline-item current"><span className="timeline-dot" /><p className="eyebrow">2024 — Present</p><h2>Green University of Bangladesh</h2><p>Department of Software Engineering<br />Current academic level: 2nd Year</p><strong>CGPA <b>3.71</b><small>/ 4.00</small></strong></div><div className="timeline-item"><span className="timeline-dot" /><p className="eyebrow">2024</p><h2>HSC</h2><p>Civil Aviation School and College</p><strong>GPA <b>4.75</b><small>/ 5.00</small></strong></div><div className="timeline-item"><span className="timeline-dot" /><p className="eyebrow">2022</p><h2>SSC</h2><p>Gulshan Model High School and College</p><strong>GPA <b>4.78</b><small>/ 5.00</small></strong></div></MotionSection><MotionSection className="achievement-panel"><GraduationCap size={24} /><p className="eyebrow">Academic achievements</p><div className="achievement"><span>02</span><h3>2nd Position</h3><p>2nd Semester</p></div><div className="achievement"><span>03</span><h3>3rd Position</h3><p>3rd Semester</p></div></MotionSection></div></div>;
}
function Activities() {
  const items = [ ['GUB Competitive Programming Community', 'Executive Member'], ['Leo Club of Green University', 'General Member'], ['Amar Somoy Amar Desh (ASAD)', 'Official Volunteer']];
  return <div className="page"><PageIntro page="activities"><p className="intro-copy">The people and communities that make the learning richer.</p></PageIntro><MotionSection className="activity-list">{items.map(([name, role], index) => <div className="activity-row" key={name}><span className="activity-count">0{index + 1}</span><div><h2>{name}</h2><p>{role}</p></div></div>)}</MotionSection><MotionSection className="quote-block"><BookOpen size={22} /><p>“Good communities make ambitious work feel possible.”</p></MotionSection></div>;
}
function Contact() {
  return <div className="page"><PageIntro page="contact"><p className="intro-copy">Whether it’s a project, an opportunity, or simply a good exchange of ideas.</p></PageIntro><div className="contact-grid contact-grid-single"><ContactForm /></div><div className="location-line"><MapPin size={16} /> Dhaka, Bangladesh <span>•</span> Available for meaningful connections</div></div>;
}

function ContactForm() {
  const [status, setStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');
  const [error, setError] = useState('');
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setError('');
    const form = event.currentTarget;
    if (!form.reportValidity()) return;
    const data = new FormData(form);
    const serviceId = import.meta.env.VITE_EMAILJS_SERVICE_ID;
    const templateId = import.meta.env.VITE_EMAILJS_TEMPLATE_ID;
    const publicKey = import.meta.env.VITE_EMAILJS_PUBLIC_KEY;
    if (!serviceId || !templateId || !publicKey) { setError('The message service is not configured yet. Please email dmasif.me@gmail.com directly.'); setStatus('error'); return; }
    setStatus('sending');
    try {
      const response = await fetch('https://api.emailjs.com/api/v1.0/email/send', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ service_id: serviceId, template_id: templateId, user_id: publicKey, template_params: { from_name: data.get('name'), from_email: data.get('email'), subject: data.get('subject'), message: data.get('message'), to_email: 'dmasif.me@gmail.com' } }) });
      if (!response.ok) throw new Error('Message could not be sent. Please try again or email me directly.');
      form.reset(); setStatus('success');
    } catch (e) { setError(e instanceof Error ? e.message : 'Something went wrong. Please try again.'); setStatus('error'); }
  };
  return <MotionSection className="contact-form-card"><p className="eyebrow">Send a message</p><form onSubmit={submit}><label>Name<input name="name" autoComplete="name" required maxLength={100} /></label><label>Email<input name="email" type="email" autoComplete="email" required maxLength={200} /></label><label>Subject<input name="subject" required maxLength={160} /></label><label>Message<textarea name="message" required minLength={10} maxLength={4000} rows={5} /></label><button className="button button-primary" type="submit" disabled={status === 'sending'}>{status === 'sending' ? 'Sending…' : 'Send message'} <ArrowUpRight size={15} /></button>{status === 'success' && <p className="form-feedback success" role="status">Thanks for reaching out. Your message was sent successfully.</p>}{status === 'error' && <p className="form-feedback error" role="alert">{error}</p>}</form></MotionSection>;
}
function WelcomeModal({ onClose, onExplore }: { onClose: () => void; onExplore: () => void }) {
  return <motion.div className="welcome-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><motion.section className="welcome-modal glass-panel" role="dialog" aria-modal="true" aria-labelledby="welcome-title" initial={{ opacity: 0, y: 18, scale: .98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 10 }} transition={{ duration: .3 }}><button className="welcome-close" onClick={onClose} aria-label="Close welcome message"><X size={18} /></button><span className="welcome-mark">A</span><p className="eyebrow">Welcome to my portfolio</p><h2 id="welcome-title">A thoughtful look at how I’m growing as an engineer.</h2><p>Thanks for stopping by. Explore my projects, experience, and the ideas I’m building toward.</p><button className="button button-primary" onClick={onExplore}>Explore portfolio <ArrowUpRight size={15} /></button></motion.section></motion.div>;
}
export default App;
