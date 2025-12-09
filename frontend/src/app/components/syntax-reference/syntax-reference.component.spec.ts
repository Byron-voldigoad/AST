import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SyntaxReferenceComponent } from './syntax-reference.component';

describe('SyntaxReferenceComponent', () => {
  let component: SyntaxReferenceComponent;
  let fixture: ComponentFixture<SyntaxReferenceComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SyntaxReferenceComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SyntaxReferenceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
