/**
 * CandleCast Mobile Navigation and Touch Interactions
 */

class MobileNavigation {
    constructor() {
        this.sidebar = null;
        this.mobileMenuBtn = null;
        this.mobileOverlay = null;
        this.isOpen = false;
        
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupMobileNav());
        } else {
            this.setupMobileNav();
        }
    }

    setupMobileNav() {
        this.createMobileElements();
        this.bindEvents();
        this.setupSwipeGestures();
        this.setupResponsiveCharts();
    }

    createMobileElements() {
        // Create mobile menu button if it doesn't exist
        if (!document.getElementById('mobileMenuBtn')) {
            const menuBtn = document.createElement('button');
            menuBtn.id = 'mobileMenuBtn';
            menuBtn.className = 'mobile-menu-btn';
            menuBtn.innerHTML = '<i class="fas fa-bars"></i>';
            document.body.appendChild(menuBtn);
        }

        // Create mobile overlay if it doesn't exist
        if (!document.getElementById('mobileOverlay')) {
            const overlay = document.createElement('div');
            overlay.id = 'mobileOverlay';
            overlay.className = 'mobile-overlay';
            document.body.appendChild(overlay);
        }

        // Get references
        this.sidebar = document.querySelector('.sidebar');
        this.mobileMenuBtn = document.getElementById('mobileMenuBtn');
        this.mobileOverlay = document.getElementById('mobileOverlay');
    }

    bindEvents() {
        if (this.mobileMenuBtn) {
            this.mobileMenuBtn.addEventListener('click', () => this.toggleSidebar());
        }

        if (this.mobileOverlay) {
            this.mobileOverlay.addEventListener('click', () => this.closeSidebar());
        }

        // Close sidebar when clicking nav links on mobile
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 768) {
                    this.closeSidebar();
                }
            });
        });

        // Handle window resize
        window.addEventListener('resize', () => this.handleResize());

        // Handle orientation change
        window.addEventListener('orientationchange', () => {
            setTimeout(() => this.handleResize(), 100);
        });

        // Prevent body scroll when sidebar is open on mobile
        document.addEventListener('touchmove', (e) => {
            if (this.isOpen && window.innerWidth <= 768) {
                if (!this.sidebar.contains(e.target)) {
                    e.preventDefault();
                }
            }
        }, { passive: false });
    }

    setupSwipeGestures() {
        let startX = 0;
        let currentX = 0;
        let isDragging = false;

        // Swipe to open from left edge
        document.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            
            // Only trigger from left edge of screen
            if (startX < 20 && !this.isOpen) {
                isDragging = true;
            }
        });

        document.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            
            currentX = e.touches[0].clientX;
            const deltaX = currentX - startX;
            
            if (deltaX > 50 && !this.isOpen) {
                this.openSidebar();
                isDragging = false;
            }
        });

        document.addEventListener('touchend', () => {
            isDragging = false;
        });

        // Swipe to close sidebar
        if (this.sidebar) {
            let sidebarStartX = 0;
            
            this.sidebar.addEventListener('touchstart', (e) => {
                sidebarStartX = e.touches[0].clientX;
            });

            this.sidebar.addEventListener('touchmove', (e) => {
                if (!this.isOpen) return;
                
                const currentX = e.touches[0].clientX;
                const deltaX = currentX - sidebarStartX;
                
                if (deltaX < -100) {
                    this.closeSidebar();
                }
            });
        }
    }

    setupResponsiveCharts() {
        // Optimize Plotly charts for mobile
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1 && node.classList.contains('plotly-graph-div')) {
                        this.optimizeChartForMobile(node);
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        // Optimize existing charts
        document.querySelectorAll('.plotly-graph-div').forEach(chart => {
            this.optimizeChartForMobile(chart);
        });
    }

    optimizeChartForMobile(chartElement) {
        if (window.innerWidth <= 768) {
            // Configure mobile-friendly layout
            const mobileLayout = {
                margin: { l: 40, r: 20, t: 40, b: 40 },
                font: { size: 10 },
                showlegend: false,
                height: 300
            };

            // Apply mobile configuration if Plotly is available
            if (window.Plotly && chartElement._fullLayout) {
                window.Plotly.relayout(chartElement, mobileLayout);
            }
        }
    }

    toggleSidebar() {
        if (this.isOpen) {
            this.closeSidebar();
        } else {
            this.openSidebar();
        }
    }

    openSidebar() {
        if (!this.sidebar) return;
        
        this.sidebar.classList.add('open');
        this.mobileOverlay.classList.add('active');
        this.isOpen = true;
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }

    closeSidebar() {
        if (!this.sidebar) return;
        
        this.sidebar.classList.remove('open');
        this.mobileOverlay.classList.remove('active');
        this.isOpen = false;
        
        // Restore body scroll
        document.body.style.overflow = '';
    }

    handleResize() {
        // Close sidebar when switching to desktop view
        if (window.innerWidth > 768 && this.isOpen) {
            this.closeSidebar();
        }

        // Re-optimize charts
        document.querySelectorAll('.plotly-graph-div').forEach(chart => {
            this.optimizeChartForMobile(chart);
        });
    }
}

// Touch-friendly table scrolling
class MobileTableHandler {
    constructor() {
        this.setupTableScrolling();
    }

    setupTableScrolling() {
        const tables = document.querySelectorAll('table');
        
        tables.forEach(table => {
            if (!table.parentElement.classList.contains('table-responsive')) {
                const wrapper = document.createElement('div');
                wrapper.className = 'table-responsive';
                table.parentNode.insertBefore(wrapper, table);
                wrapper.appendChild(table);
            }
        });
    }
}

// Mobile-optimized form handling
class MobileFormHandler {
    constructor() {
        this.setupFormOptimizations();
    }

    setupFormOptimizations() {
        const inputs = document.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            // Prevent zoom on iOS when focusing inputs
            if (input.type !== 'range' && input.type !== 'checkbox' && input.type !== 'radio') {
                const currentFontSize = window.getComputedStyle(input).fontSize;
                if (parseFloat(currentFontSize) < 16) {
                    input.style.fontSize = '16px';
                }
            }

            // Add touch-friendly styling
            input.style.minHeight = '48px';
            
            // Optimize number inputs for mobile
            if (input.type === 'number') {
                input.setAttribute('inputmode', 'numeric');
                input.setAttribute('pattern', '[0-9]*');
            }
        });
    }
}

// Mobile performance optimizations
class MobilePerformanceOptimizer {
    constructor() {
        this.setupLazyLoading();
        this.optimizeAnimations();
    }

    setupLazyLoading() {
        // Lazy load sparklines and charts when they come into view
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    
                    if (element.classList.contains('sparkline-container')) {
                        this.loadSparkline(element);
                    }
                    
                    observer.unobserve(element);
                }
            });
        }, {
            rootMargin: '50px'
        });

        document.querySelectorAll('.sparkline-container, .chart-container').forEach(el => {
            observer.observe(el);
        });
    }

    loadSparkline(container) {
        // Trigger sparkline loading if not already loaded
        if (!container.hasAttribute('data-loaded')) {
            container.setAttribute('data-loaded', 'true');
            
            // Dispatch custom event for sparkline initialization
            const event = new CustomEvent('loadSparkline', {
                detail: { container }
            });
            document.dispatchEvent(event);
        }
    }

    optimizeAnimations() {
        // Reduce animations on mobile for better performance
        if (window.innerWidth <= 768) {
            const style = document.createElement('style');
            style.textContent = `
                *, *::before, *::after {
                    animation-duration: 0.1s !important;
                    animation-delay: 0s !important;
                    transition-duration: 0.1s !important;
                    transition-delay: 0s !important;
                }
            `;
            
            // Only add if user prefers reduced motion
            if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                document.head.appendChild(style);
            }
        }
    }
}

// Initialize mobile functionality
document.addEventListener('DOMContentLoaded', function() {
    new MobileNavigation();
    new MobileTableHandler();
    new MobileFormHandler();
    new MobilePerformanceOptimizer();
    
    // Add mobile class to body for CSS targeting
    if (window.innerWidth <= 768) {
        document.body.classList.add('mobile');
    }
    
    window.addEventListener('resize', function() {
        if (window.innerWidth <= 768) {
            document.body.classList.add('mobile');
        } else {
            document.body.classList.remove('mobile');
        }
    });
});

// Export for use in other scripts
window.CandleCastMobile = {
    MobileNavigation,
    MobileTableHandler,
    MobileFormHandler,
    MobilePerformanceOptimizer
};